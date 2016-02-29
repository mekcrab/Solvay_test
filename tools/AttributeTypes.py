'''
Module contains class definitions for various types of attibutes encountered during testing

'''

__author__ = 'ekoapche'
import time


class Attribute_Base(object):
    '''Base class for various types of system . Contains hooks, method stubs and normalized instance
        attributes for derivative classes.'''

    def __init__(self, *args):
        self.attrs = list()  # TODO: what does this actually mean? should an attribute be only a single value?

        self.complete = False  # value of attribute evaluation - set in self.evaluate method

        self.data = list()  # list of timeseries data for trending/saving

    def add_attribute(self,attribute):
        '''Adds an attribute to the base list of attribute'''
        # fixme - see attribute one:many vs. one:one relation comment in self.__init__
        if not isinstance(attribute, Attribute_Base):
            raise TypeError
        else:
            self.attrs.append(attribute)

    def save_value(self, value):
        '''Adds a timestamp, value tuple to this attribute's self.data
        for later retrieval and analysis
        :param: value - any serializable object (ex. float, string, "condition object", tuples ...)
        '''
        self.data.append((time.time, value))

    def read(self):
        '''Stub for reading a value for this attribute
        Set instance attribute self.readhook in subclasses or at runtime via self.set_read_hook.

        :return: value read from system.'''
        return self.readhook()

    def set_read_hook(self, readhook):
        self.readhook = readhook

    def write(self, value):
        '''Stub for writing to this attribute's value.
        :return: sucess of write'''
        return self.writehook(value)

    def set_write_hook(self, writehook):
        self.writehook = writehook

    def evaluate(self):
        #TODO: How do we evaluate if an attribute complete? (EFK comment: subclass and override evaluate there
        '''set value of self.complete here'''
        raise NotImplementedError

    def set_complete(self):
        '''Sets the self.complete parameter to be True or False depending on results of self.evaluate'''
        raise NotImplementedError


class DiscreteAttribute(Attribute_Base):
    '''Base class for discrete attributes
        Examples:   NamedSets, Binary/Boolean, Bitmask'''

    def evaluate(self):
        pass


class NamedDiscrete(DiscreteAttribute):
    '''Sublcass for attributes with string name mappings to integer values'''
    def __init__(self, int_dict = {}):
        self.int_dict = int_dict


class DiscreteCondition(DiscreteAttribute):
    def evaluate(self):
        '''Evaluates if discrete condition is true'''
        pass


class AnalogAttribute(Attribute_Base):
    '''Base class for analog/continuously valued attributes
        Examples: PV, SP, floating point, 16/32 bit integers (ex. modbus values)
    '''
    def evaluate(self):
        return self.complete
    

class AnalogCondition(AnalogAttribute):

    def __init__(self, target_value, operator = '=', value_tolerance = 0.01):
        self.val_tol = value_tolerance
        self.target = target_value
        self.operator = operator  # single character of operator type

        AnalogAttribute.__init__(self)

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
        return AnalogAttribute.evaluate(self)


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

    def __init__(self):
        NamedDiscrete.__init__(self, ModeAttribute.target_int_dict)

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

    def __init__(self):
       NamedDiscrete.__init__(self, int_dict=StatusAttribute.status_int_dict)
