'''
Module contains class definitions for various types of attibutes encountered during testing

'''

import time

__author__ = 'ekoapche'


class Attribute_Base(object):
    '''Base class for various types of system . Contains hooks, method stubs and normalized instance
        attributes for derivative classes.'''

    def __init__(self, tag, *args, **kwargs):
        self.tag = tag  # root tag

        self.attr_path = kwargs.pop('attr_path', '')  # attribute path from tag designation, defaults to empty string

        self.complete = None  # value of attribute evaluation - set in self.evaluate method.
                              # Nonetype means not yet evaluated

        self.data = list()  # list of timeseries data for trending/checking historical data

    def __str__(self):
        '''String method for base attribute - can be overridden in subclasses'''
        return self.OPC_path()

    def __add__(self, other):
        '''Logical OR of attributes - disjunction of attribute.complete parameters
           Note: True or None returns True'''
        return self.complete or other.complete

    def __mul__(self, other):
        '''Logical AND of attributes - conjunction of attribute.complete parameters.
            Note "True and None" returns None'''
        return self.complete and other.complete

    # TODO: decide if __enter__ and __exit__ methods are appropriate for running self.evaluate in a
    # TODO:     with xxx as yyy: context - perhaps used to set readhook/writehook or add to OPC tag group?

    def set_attr_path(self, attribute_path):
        '''Adds an attribute to the base tag. '''
        # todo: evaluate if this is a valid attribute based on self.tag
        self.attr_path = attribute_path

    def save_value(self):
        '''Adds a timestamp, value tuple to this attribute's self.data
        for later retrieval and analysis
        :param: value - any serializable object (ex. float, string, "condition object", tuples ...)
        '''
        self.data.append((time.time, self.read()))

    def read(self, param='CV'):
        '''Stub for reading a value for this attribute
        Set instance attribute self.readhook in subclasses or at runtime via self.set_read_hook.
        :return: value read from system.'''
        read_path = self.OPC_path() + '.' + param
        return self.readhook(read_path)

    def set_read_hook(self, readhook):
        self.readhook = readhook

    def write(self, value, param='CV'):
        '''Stub for writing to this attribute's value.
        :return: sucess of write'''
        write_path = self.OPC_path() + '.' + param
        return self.writehook( (write_path, value) )

    def set_write_hook(self, writehook):
        self.writehook = writehook

    def set_complete(self, complete=False):
        '''Sets the self.complete parameter to be True or False depending on results of self.evaluate'''
        self.complete = complete
        return self.complete

    def OPC_path(self):
        '''
        Prints the OPC path of this attribute
        '''
        return str(self.tag) + str(self.attr_path)

    def evaluate(self):
        '''
        Sets value of self.complete based on read/write method combination as required.
        Attribute_Base instances implements a dummy method, always returning false.'''
        return self.set_complete(complete=False)


class DiscreteAttribute(Attribute_Base):
    '''Base class for discrete attributes
        Examples:   NamedSets, Binary/Boolean, Bitmask'''

    def evaluate(self):
        raise NotImplementedError


class NamedDiscrete(DiscreteAttribute):
    '''Sublcass for attributes with string name mappings to integer values'''
    def __init__(self, tag, int_dict = {}, attr_path=''):
        self.int_dict = int_dict
        Attribute_Base.__init__(self, tag, attr_path=attr_path)

    def evaluate(self):
        raise NotImplementedError

class DiscreteCondition(DiscreteAttribute):

    def evaluate(self):
        '''Evaluates if discrete condition is true'''
        raise NotImplementedError


class AnalogAttribute(Attribute_Base):
    '''Base class for analog/continuously valued attributes
        Examples: PV, SP, floating point, 16/32 bit integers (ex. modbus values)
    '''
    def evaluate(self):
        raise NotImplementedError


class AnalogCondition(AnalogAttribute):

    def __init__(self, tag, target_value, operator='=', value_tolerance = 0.01, attr_path=''):
        self.val_tol = value_tolerance
        self.target = target_value
        self.operator = operator  # single character of operator type

        AnalogAttribute.__init__(self, tag, attr_path=attr_path)

    def evaluate(self):
        '''
        Evaluates analog comparision: <, >, = (within tolerance), != (within tolerance)
        '''
        # gather required parameters to build python expression
        current_value = self.read()
        # read a target value from the system if required
        if isinstance(self.target, Attribute_Base):
            target = self.target.read()
        else:
            target = self.target
        # this string will be evaluated as a python expression
        expr = ''.join([str(current_value), self.operator, str(target)])

        # evaluate condition
        cnd_val = eval(expr)

        # check tolerance
        # fixme: add tolerance band (will be based on operator type....)

        # return result
        self.complete = cnd_val
        # call parent method to complete
        return self.complete


class ModeAttribute(NamedDiscrete):
    '''
    Unique class of attribute for evaluation of DeltaV modes
    '''
    # integer mapping of mode values to MODE.TARGET
    # --> used for writes by default
    target_int_dict = {'LO':4, 'MAN':8, 'AUTO' : 16, 'CAS' : 48, 'ROUT':144, 'RCAS':80}

    # integer mapping MODE.ACTUAL (not sure why these are different...)
    # --> used for reads by default
    actual_int_dict = \
        {'LO' : 4, 'MAN' : 8, 'AUTO' : 16, 'CAS' : 32, 'ROUT':128, 'RCAS':64}

    def __init__(self, tag, attr_path=''):
        NamedDiscrete.__init__(self, tag, int_dict=ModeAttribute.target_int_dict, attr_path=attr_path)

    def write(self, val):
        '''Writes are directed to MODE.TARGET'''
        if type(val) in [str, unicode]:
            val = ModeAttribute.target_int_dict[val]
        Attribute_Base.write(val, param='TARGET')

    def read(self):
        '''Reads are directed to MODE.ACTUAL'''
        Attribute_Base.read(self, param='ACTUAL')

    def evaluate(self):
        raise NotImplementedError

class StatusAttribute(NamedDiscrete):
    '''
    Unique class of attribute for evaluation of OPC status
    '''
    # dictionary of status names to integer values
    status_int_dict = {
        'BAD': 0,
        'GOOD': 128,
        # etc...
    }

    def __init__(self, tag, attr_path=''):
       NamedDiscrete.__init__(self, tag, int_dict=StatusAttribute.status_int_dict, attr_path=attr_path)



class PromptAttribute(NamedDiscrete):
    '''
    Unique class of attribute for OAR prompts
    '''
    OAR_int_dict = {
        'YES': 1,
        'NO': 0,
        'OK': 1
        #FP/INT, etc...
    }

    def __init__(self, attr_path =''):
        NamedDiscrete.__init__(self, tag = '^/FAIL_MONITOR/OAR', int_dict=ModeAttribute.target_int_dict, attr_path=attr_path)

    def write(self, input):
        '''write input (YES/NO/OK/FP/INT) to  '^/FAIL_MONITOR/OAR/INPUT'''
        pass

    def read(self):
        '''
        :return:'^/P_MSG1.CV', '^/P_MSG2.CV', '^/FAIL_MONITOR/OAR/TYPE.CV'
        '''
        pass

class PositionAttribute(AnalogCondition):
    '''
    Unique class of attribute for Valve/Pump position
    '''

    def __init__(self, tag):
        AnalogCondition.__init__(self, tag, target_value = self.target, operator='=', value_tolerance = 0.01, attr_path='')

    def write(self, target_value):
        self.target = target_value
        pass

    def read(self):
        pass

class InicationAttribute(AnalogCondition):
    '''
    Unique class of attribute for PV indication.
    Ex: Flow Rate (FIC), Tank Level, PH, Pressure (PIC), Temperature (TI), Tank Weight, etc.
    '''

    def __init__(self, tag):
        AnalogCondition.__init__(self, tag, target_value = self.target, operator='=', value_tolerance = 0.01, attr_path='')


    def read(self):
        pass


class EMCMDAttribute(NamedDiscrete):
    #TODO: import EMCMD dictionary to EMCMD_int_dict
    EMCMD_int_dict = {

    }

    def __int__(self, tag):
        pass


class PhaseCMDAttribute(NamedDiscrete):
    #TODO: import Phase Command dictionary to PhaseCMD_int_dict

    def __int__(self):
        pass


class OtherAttribute(AnalogCondition):
    '''
    class for all other kind of attribute
    '''
    def __init__(self, tag):
        AnalogCondition.__init__(self, tag, target_value = self.target, operator='=', value_tolerance = 0.01, attr_path='')

    def read(self):
        pass

    def write(self, target_value):
        pass
