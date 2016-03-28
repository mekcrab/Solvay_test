'''

Module contains base class deifnition for AttributeTypes.

Should fully define abstracted Attribute class interface

'''

import time

from tools.Utilities.Logger import LogTools
dlog = LogTools('AttributeTypes.log', 'AttributeBase')
dlog.rootlog.warning('AttributeBase initialized')

class AttributeBase(object):
    '''Base class for various types of system . Contains hooks, method stubs and normalized instance
        attributes for derivative classes.'''

    def __init__(self, tag, **kwargs):
        '''
        Constructor
        :param tag: OPC tag of the attribute's parent module
        :param kwargs:
        :return:
        '''
        self.tag = tag  # root tag

        if 'attr_path' in kwargs:
            attr_str = kwargs.pop('attr_path').split('.')
            self.attr_path = attr_str[0] # attribute path from tag designation, defaults to empty string
            if len(attr_str) > 1:
                self.param = attr_str[1]

        if hasattr(self, 'target_value'):
            pass  # self.target_value inherited from child class __init__()
        else:
            self.target_value = kwargs.pop('target_value', None)  # default target_value for testing

        self.raw_string = kwargs.pop('raw_string', '')  # string from which this attribute was parsed

        # internal plumbing
        self._complete = None   # value of attribute evaluation - set in self.evaluate method.
                                # Nonetype means not yet evaluated
        self.active = False  # flag to indicate if the self.execute() method should be evaluated during a test

        self.data = list()  # list of timeseries data for trending/checking historical data
        self.exe_cnt = 0    # number of times self.execute() has been called
        self.exe_start = None  # internal timer, intended to be initiated on call to self.execute

        self._default_test = None  # function hook to set default testing behavior of execute

    def __str__(self):
        '''String method for base attribute - can be overridden in subclasses'''
        return self.OPC_path()

    def __repr__(self):
        '''Method for printing the object identity'''
        return self.__class__.__name__ + ': ' + self.OPC_path()

    def __add__(self, other):
        '''Logical OR of attributes - disjunction of attribute.complete parameters
           Note: True or None returns True'''
        return self._complete or other._complete

    def __mul__(self, other):
        '''Logical AND of attributes - conjunction of attribute.complete parameters.
            Note "True and None" returns None'''
        return self._complete and other._complete

    def _read(self, param='CV'):
        '''Stub for reading a value for this attribute
        Set instance attribute self.readhook in subclasses or at runtime via self.set_read_hook.
        :return: value read from system.'''
        read_path = self.OPC_path() + '.' + param
        return self.readhook(read_path)

    def set_read_hook(self, readhook):
        self.readhook = readhook

    def _write(self, value, param='CV'):
        '''Stub for writing to this attribute's value.
        :return: sucess of write'''
        write_path = self.OPC_path() + '.' + param
        return self.writehook(write_path, value)

    def set_write_hook(self, writehook):
        self.writehook = writehook

    def set_target_value(self, target_value):
        '''
        Sets default testing parameter self.target_value
        '''
        self.taget_value = target_value

    def set_complete(self, complete=False):
        '''Sets the self.complete parameter to be True or False depending on results of self.evaluate'''
        self._complete = complete
        return self._complete

    def activate(self):
        self._active = True

    def deactivate(self):
        self._active = False

    def OPC_path(self):
        '''
        Prints the OPC path of this attribute
        '''
        return '/'.join([str(self.tag), str(self.attr_path)])

    def start_timer(self):
        '''Starts the attribute's internal timer'''
        self.exe_start = time.time()

    def stop_timer(self):
        '''Stops the attribute's internal timer'''
        self.exe_start = None

    def restart_timer(self):
        '''Resets attribute's internal timer'''
        self.start_timer()

    def get_timer(self):
        '''Returns elapsed time since start_timer or restart_timer call'''
        return time.time() - self.exe_start

    def execute(self):
        '''
        Execute "Set" or "Compare" (read/write)
        commands in the attributes and flag is_complete parameter.

        Base method is a dummy - sets itself to True after 10 executions.
        '''
        if self.exe_cnt < 1:
            self.start_timer()
        elif self.exe_cnt > 10:
            return self.set_complete(True)

        self.exe_cnt += 1
        return self.set_complete(False)

    def force(self):
        '''Forces a value, if possible. Used for write-based tests or forcing stuck values'''
        raise NotImplementedError

    def save_value(self):
        '''Adds a timestamp, value tuple to this attribute's self.data
        for later retrieval and analysis
        :param: value - any serializable object (ex. float, string, "condition object", tuples ...)
        '''
        self.data.append((time.time(), self._read()))

