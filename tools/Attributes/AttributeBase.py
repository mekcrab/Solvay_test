'''

Module contains base class deifnition for AttributeTypes.

Should fully define abstracted Attribute class interface

'''

import time
import copy

from tools.Utilities.Logger import LogTools
dlog = LogTools('AttributeTypes.log', 'AttributeBase')
dlog.rootlog.warning('AttributeBase initialized')


class AttributeBase(object):
    '''Base class for various types of system . Contains hooks, method stubs and normalized instance
        attributes for derivative classes.'''

    base_log = dlog

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
        elif not hasattr(self, 'attr_path'):
            self.attr_path = ''

        if hasattr(self, 'target_value'):
            pass  # self.target_value inherited from child class __init__()
        else:
            self.target_value = kwargs.pop('target_value', None)  # default target_value for testing

        self.raw_string = kwargs.pop('raw_string', '')  # string from which this attribute was parsed

        # initial log for instantiation
        #   should be set to a test-specific execution log during test case execution
        #   with self.set_log
        self.logger = dlog.MakeChild(self.__repr__())

        # internal plumbing
        self._complete = None   # value of attribute evaluation - set in self.evaluate method.
                                # Nonetype means not yet evaluated

        self._active = False  # flag to indicate if the self.execute() method should be evaluated during a test

        self.data = list()  # list of timeseries data for trending/checking historical data
        self.last_read = None  # most recent read value

        # execution timers/counters
        self.exe_cnt = 0    # number of times self.execute() has been called
        self.exe_start = None  # internal timer, intended to be initiated on call to self.execute
        self.exe_time = None  # total execution time once self._complete

        self._default_test = kwargs.pop('default_test', 'check_value')  # function hook to set default testing behavior of execute

        self._test_types = {  # test types available to this AttributeType class
                            'check_value': 'check_value',
                            'force_value': 'force'
        }

        self._execute = None  # private execute method called by self.execute administative wrapper

        self.set_execute()  # sets self._execute to another bound instance method

        self.logger.debug('New instance created: %r', self)

    def __str__(self):
        '''String method for base attribute - can be overridden in subclasses'''
        return self.OPC_path()

    def __repr__(self):
        '''Method for printing the object identity'''
        return self.__class__.__name__ + ': ' + self.OPC_path()

    def __eq__(self, other):
        '''Method to determine if two attributes are equivalent by comparing their OPC paths'''
        return self.OPC_path() == other.OPC_path()

    def __add__(self, other):
        '''Logical OR of attributes - disjunction of attribute.complete parameters
           Note: True or None returns True'''
        return self._complete or other._complete

    def __mul__(self, other):
        '''Logical AND of attributes - conjunction of attribute.complete parameters.
            Note "True and None" returns None'''
        return self._complete and other._complete

    def copy(self, copy_all=False):
        '''Creates a copy of the attribute. Underlying attribute are copied with the copy_all flag'''
        # dereference 'uncopyable' items, create deep copy, then rebind

        # internally bound methods/exeternal objects
        logger = self.logger; self.logger = None
        _execute = self._execute; self._execute = None

        # attributes contained in this module
        embedded_attrs = self.get_embedded_attrs()
        new_embedded = dict()
        for name, attr in embedded_attrs.items():
            if copy_all:
                new_embedded[name] = attr.copy()
            else:
                new_embedded[name] = attr
            setattr(self, name, None)
            # embedded_attrs.pop(name)

        attr_copy = copy.deepcopy(self)  # creates a copy of all remaining bound data structures

        for k,v in embedded_attrs.items():
            setattr(self, k, v)
            setattr(attr_copy, k, new_embedded[k])

        attr_copy.logger = logger; self.logger = logger
        attr_copy._execute = _execute; self._execute = _execute

        return attr_copy

    def set_log(self, log_tool, level = None):
        '''Sets self.logger to be a child of the new_log,
        embedded attributes become children of self.logger'''
        if isinstance(log_tool, LogTools):
            self.logger = log_tool.MakeChild(self.__repr__(), level)
            # set child log of all embedded attributes
            for k, v in self.get_embedded_attrs().items():
                v.set_log(log_tool)
            self.logger.debug('Logger set to %s', self.logger.name)
        else:
            raise TypeError

    def get_embedded_attrs(self):
        '''Returns a dictionary of AttributeBase instances which are (python) attributes of this AttributeBase instace'''
        return dict([(k,v) for k,v in self.__dict__.items() if isinstance(v, AttributeBase)])

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

    def get_complete(self):
        '''Returns boolean value if the execution of this attribute is complete'''
        return self._complete

    def set_complete(self, complete=False):
        '''Sets the self.complete parameter to be True or False depending on results of self.evaluate'''
        self._complete = complete
        return self._complete

    def activate(self):
        '''Sets self._activate flag True, indicating this attribute should actively be calling self.execute()
         during test execution'''
        self._active = True

    def deactivate(self):
        '''Sets self._activate flag False, indicating this attribute should no longer calling self.execute()
        during test execution'''
        self._active = False

    def is_active(self):
        '''Method to check if this attribute is currently active'''
        return self._active

    def OPC_path(self):
        '''
        Prints the OPC path of this attribute
        '''
        if self.attr_path:
            return '/'.join([str(self.tag), str(self.attr_path)])
        else:
            return self.tag

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

    def check_value(self):
        '''
        Baseline read-only testing method, to be overridden in subclasses.
        Base method is a dummy - sets itself to True after 10 executions.
        '''
        if self.exe_cnt > 10:
            return self.set_complete(True)
        else:
            return self.set_complete(False)

    def force(self):
        '''Forces a value, if possible. Override in subclasses'''
        raise NotImplementedError

    def execute(self):
        '''Default method called by TestAdmin - can be set to an arbitration function hook as depending on
        the demands of the system under test
        '''
        self.exe_cnt += 1
        self.logger.debug("Execute call, count = %d", self.exe_cnt)
        # start timer on first call to self.execute or when self._complete is false
        if not self.exe_start and self._complete:
            self.start_timer()

        exe = self._execute()  # should return boolean value of successfulunsuccessfull execution

        if self._complete and not exe:  # set total execution time in seconds on PDET
            self.exe_time += self.get_timer();
            self.stop_timer()
            self.logger.info('Execute set complete after %.2f seconds', self.exe_time)
        return exe

    def set_execute(self, test_method=None):
        '''
        Sets self.execute method dynamically as the test requires. Should be overridden as appropriate in subclasses
        :return:
        '''
        if not test_method:
            test_method = self._test_types[self._default_test]
        self._execute = getattr(self, test_method)
        self.logger.info('Execute method set to %r', self._execute)

    def save_value(self):
        '''Adds a timestamp, value tuple to this attribute's self.data
        for later retrieval and analysis
        :param: value - any serializable object (ex. float, string, "condition object", tuples ...)
        '''
        self.data.append((time.time(), self._read()))


class AttributeDummy(AttributeBase):
    '''
    Dummy attribute for:
        testing, as a placeholder, or deferring attributes type differentiation'''

    def __init__(self, id='', **kwargs):
        '''Constructor'''
        self.id = id
        AttributeBase.__init__(self, 'dummy', **kwargs)

    def read(self):
        self.logger.debug('Dummy read ', self.id)
        return self.id

    def write(self, val=0):
        self.logger.debug('Dummy write', self.id, 'as ', val)

    def execute(self):
        self.logger.debug('Dummy execute', self.id)
        if not self._complete:
            self.deactivate()
            return self.set_complete(True)
        else:
            return self.set_complete(True)

    def force(self):
        self.logger.debug('Dummy force')
        self.set_complete(True)
