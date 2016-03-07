'''
Module contains class definitions for various types of attibutes encountered during testing


Attributes are separated into two major sub categories: execution and data
    execution categories:     based on execution method involving
        subtypes:
            * write, write followed by read confirmation
            * computation based on repeated writes
            * logical comparison (including checking for equivalency based on read value)

    data categories:        based on the data type of the OPC parameter
        subtypes:
            * boolean - value is either true or false, written/read as 1 or 0
            * named set - value is based on a string<->integer mapping, written/read as integer
            * mode (special type of named set) - value is based on special MODE attribute;
                                                    written as MODE.TARGET, read as MODE.ACTUAL
            * command (special type of named set) - specifically for reading/writing EM and phase commands
            * status (special type of named set) - used to read .ST attributes, that is, OPC status values
            * string - value is a string, written/read as a string datatype
            * floating point - value is floating point
            * SP/PV (special type of floating point, boolean, or named set) - reads/writes depend on MODE

All attribute classes should be defined as a mixin of one or more parent
    classes from each execution and data categories. For example, closing a valve would be a combination
    of execution subtype <write> combined with data subtypes <boolean> <mode> and <SP/PV>.
'''

import time

__author__ = 'ekoapche'


class Attribute_Base(object):
    '''Base class for various types of system . Contains hooks, method stubs and normalized instance
        attributes for derivative classes.'''

    def __init__(self, tag, *args, **kwargs):
        self.tag = tag  # root tag

        self.attr_path = kwargs.pop('attr_path', '')  # attribute path from tag designation, defaults to empty string

        self.raw_string = kwargs.pop('raw_string', '')  # string from which this attribute was parsed

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

   # def set_attr_path(self, attribute_path):
   #     '''Adds an attribute to the base tag. '''
   #     # todo: evaluate if this is a valid attribute based on self.tag
   #     self.attr_path = attribute_path

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

############################# State Attribute Types (Set Values) ##############################

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


    def __init__(self, tag, attr_path='MODE'):
        NamedDiscrete.__init__(self, tag, int_dict=ModeAttribute.target_int_dict, attr_path=attr_path)

    def setmode(self, mode):
        '''Writes are directed to MODE.TARGET '''
        if type(mode) in [str, unicode]:
            mode = ModeAttribute.target_int_dict[mode]
        Attribute_Base.write(mode, param='TARGET')

    def checkmode(self):
        '''Reads are directed to MODE.ACTUAL'''
        Attribute_Base.read(self, param='ACTUAL')

    def evaluate(self):
        raise NotImplementedError


class PositionAttribute(NamedDiscrete):
    '''
    Unique class of attribute for Valve/Pump position
    '''
    bool_position_dict = {'OPEN' : 1, 'CLOSE': 0,
                     'OPENED': 1, 'CLOSED': 0,
                     'START': 1, 'STOP': 0,
                     'RUNNING': 1, 'STOPPED': 0}

    modenum_str_dict = {16: 'AUTO', 32 : 'CAS', 48: 'CAS', 128: 'ROUT', 144 : 'ROUT', 64: 'RCAS', 80:'RCAS'}

    # mode:attr_path dictionary --> used for writes by default
    mode_act_dict = {'AUTO' : 'SP_D', 'CAS' : 'REQ_SP', 'ROUT':'REQ_OUTP', 'RCAS':'REQ_SP'}

    # mode: attr_path dictionary--> used for reads by default
    mode_confim_dict = {'AUTO' : 'PV_D', 'CAS' : 'PV_D', 'ROUT':'OUTP', 'RCAS':'PV_D'}

    def __init__(self, tag, attr_path =''):
        self.attr_path = attr_path
        self.tag = tag
        NamedDiscrete.__init__(self, tag, int_dict=PositionAttribute.bool_position_dict, attr_path=self.attr_path)

    def set(self, target_value, mode):
        '''
        :param: target_value can be a boolean number or str(Open/close/start/stop...)
        :param: mode can be int, str or unicode
        '''

        if target_value in [str, unicode]:
            target_value = target_value.upper()
            target_value = PositionAttribute.bool_position_dict[target_value]

        if type(mode) in [str, unicode]:
            mode = mode.upper()
        elif type(mode) in [int]:
            mode = PositionAttribute.modenum_str_dict[mode]

        self.attr_path = PositionAttribute.mode_act_dict[mode]
        Attribute_Base(tag = self.tag, attr_path = self.attr_path).write(target_value)

    def checkposition(self):
        Attribute_Base(tag = self.tag, attr_path = self.attr_path).read()


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


class PromptAttribute(Attribute_Base):
    '''
    Unique class of attribute for OAR prompts
    '''
    OAR_int_dict = {
        'YES': 1,
        'NO': 0,
        'OK': 1
        #FP/INT, etc...
    }

    OAR_Type_dict = {
        'YES': 'YES/NO',
        'NO': 'YES/NO',
        'OK': 'OK'

    }

    Type_int_dict = {
        'RESET': 0,
        'NONE': 1,
        'INT - NO LIMITS': 2,
        'INT - WITH LIMITS': 3,
        'FP - NO LIMITS': 4,
        'FP - WITH LIMITS': 5,
        'YES/NO': 6,
        'OK': 7,
        'STRING': 8

    }
    class_path_dict = {'PHASE': 'FAIL_MONITOR', 'EM': 'MONITOR'}

    def __init__(self, Class, tag, attr_path =''):
        '''

        :param Class: define if it's a phase or EM
        :param tag: should be the phase or EM instance name
        :param attr_path:
        :return:
        '''
        self.tag = tag
        self.Class = Class.upper()
        Attribute_Base.__init__(self, tag, attr_path=attr_path)

    def answer(self, input):
        '''read prompt, define the prompt type, then write input (YES/NO/OK/FP/INT) to
        '^/FAIL_MONITOR/OAR/INPUT' for phase classes and '^/MONITOR/OAR/INPUT' for EM classes
        '''

        input_type = 1
        if input in [str, unicode]: # If input is Yes/No or OK
            self.input = input.upper()
            input_type = PromptAttribute.OAR_Type_dict[self.input] # Capitalized input
            if self.input in PromptAttribute.OAR_int_dict:
                input = PromptAttribute.OAR_int_dict[self.input]

        #TODO: Verify if it's answering the right question. Maybe do it in the generator?
        #TODO: My thought was to pull out the OAR_MSG and OAR_Type with readprompt function and compare.
        #if input_type == OAR_Type and keyword in OAR_MSG:

        self.input_path = PromptAttribute.class_path_dict[self.Class] + 'OAR/INPUT'
        Attribute_Base(self.tag, attr_path = self.input_path).write(input)

    def readprompt(self):
        OAR_Type = 1
        if self.Class in PromptAttribute.class_path_dict:
            self.oar_path = PromptAttribute.class_path_dict[self.Class] + 'OAR/TYPE'
            OAR_Type = Attribute_Base(self.tag, attr_path = self.oar_path).read()
        MSG1 = Attribute_Base(self.tag, attr_path = 'P_MSG1').read()
        MSG2 = Attribute_Base(self.tag, attr_path = 'P_MSG2').read()

        return (OAR_Type, MSG1, MSG2)


class InicationAttribute(Attribute_Base):
    '''
    Unique class of attribute for PV indication.
    Ex: Flow Rate (FIC), Tank Level, PH, Pressure (PIC), Temperature (TI), Tank Weight, etc.
    Indicators use AI1 or INT1 functional blocks
    '''

    def __init__(self, tag):
        self.tag = tag
        Attribute_Base.__init__(self, tag, attr_path = '')

    def indicate(self):
        # TODO: need to verify which value (AI1 or INT1) is readable
        AI1 = Attribute_Base(tag = self.tag, attr_path = 'AI1/OUT').read()
        INT1 = Attribute_Base(tag = self.tag, attr_path = 'INT1/OUT').read()
        return AI1, INT1


class EMCMDAttribute(Attribute_Base):
    #TODO: import EMCMD dictionary to EMCMD_int_dict
    EMCMD_int_dict = {

    }

    def __int__(self, tag, attr_path = ''):
        ''' :param: tag: the name of EM class
        '''
        self.attr_path = attr_path
        self.tag = tag
        Attribute_Base.__init__(self, tag, attr_path=self.attr_path)

    def set(self, command):
        self.attr_path = 'A_COMMAND'
        if command in [str, unicode]:
            command = EMCMDAttribute.EMCMD_int_dict[command]
        Attribute_Base(tag = self.tag, attr_path = self.attr_path).write(command)

    def checkcmd(self):
        self.attr_path = 'A_TARGET'
        return Attribute_Base(tag = self.tag, attr_path = self.attr_path).read()


class PhaseCMDAttribute(NamedDiscrete):
    #TODO: import Phase Command dictionary to PhaseCMD_int_dict
    #TODO: Which attr_path are we using to run a phase???

    def __int__(self):
        pass


class OtherAttribute(Attribute_Base):
    '''
    class for all other kind of attribute
    '''
    def __init__(self, tag, attr_path, param = 'CV'):
        self.param = param
        Attribute_Base.__init__(self, tag, attr_path)

    def read(self):
        Attribute_Base.read(self, param = self.param)

    def write(self, target_value):
        Attribute_Base.write(self, value = target_value, param = self.param)


#####################Transition Attribute Types (use read functions and compare) #########################
class ComparisonAttributes:
    #TODO: Get system values with the read functions above
    pass


if __name__ == "__main__":
    from tools.serverside.OPCclient import OPC_Connect

    connection = OPC_Connect()

    m1 = ModeAttribute('CV-1423', 'DC1/MODE')
    m2 = ModeAttribute('CV-3854', 'MODE')

    attrs = [m1, m2]

    for attr in attrs:
        attr.set_read_hook(connection.read)
        attr.set_write_hook(connection.write)
