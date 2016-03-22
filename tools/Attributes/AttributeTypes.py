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

import time, os
import tools.config as config
from tools.Utilities.Logger import LogTools
import operator

__author__ = 'ekoapche'

dlog = LogTools(config.log_path + 'AttributeTypes.log', config.log_level, 'AttributeTypes')
dlog.rootlog.warning('AttributeTypes initialized')


class Attribute_Base(object):
    '''Base class for various types of system . Contains hooks, method stubs and normalized instance
        attributes for derivative classes.'''

    def __init__(self, tag, *args, **kwargs):
        self.tag = tag  # root tag
        self.attr_path = kwargs.pop('attr_path', '')  # attribute path from tag designation, defaults to empty string
        self.raw_string = kwargs.pop('raw_string', '')  # string from which this attribute was parsed

        self._complete = None  # value of attribute evaluation - set in self.evaluate method.
                                 # Nonetype means not yet evaluated
        self.active = False  # flag to indicate if the self.execute() method should be evaluated during a test

        self.data = list()  # list of timeseries data for trending/checking historical data
        self.exe_cnt = 0  # number of times self.execute() has been called
        self.exe_start = 0  # internal timer, intended to be initiated on call to self.execute

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
        return self.writehook(write_path, value)

    def set_write_hook(self, writehook):
        self.writehook = writehook

    def set_complete(self, complete=False):
        '''Sets the self.complete parameter to be True or False depending on results of self.evaluate'''
        self.complete = complete
        return self.complete

    def activate(self):
        self._active = True

    def deactivate(self):
        self._active = False

    def OPC_path(self):
        '''
        Prints the OPC path of this attribute
        '''
        return os.path.join(str(self.tag), str(self.attr_path))

    def start_timer(self):
        self.exe_start = time.time()

    def get_timer(self):
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
        self.data.append((time.time(), self.read()))


class Constant(Attribute_Base):
    '''Attribute wrapper for constant values like numbers, strings, etc'''

    def __init__(self, value, *args, **kwargs):

        if type(value) in [int, float, str, unicode]:
            self.val = value
        else:
            raise TypeError
        Attribute_Base.__init__(self, 'Constant', path=value)

    def read(self):
        return (self.val, 'Good', time.ctime())

    def write(self, value):
        self.val = value
        return 'Success'


class Compare(Attribute_Base):

    def __init__(self, lhs, opr, rhs, deadband=0):
        '''
        Comparison between two sub-attributes in the form of:
            (left hand side) (operator) (right hand side)
        Ex: PI-1783 > 65
        Both rhs and lhs must be sub classes of Attribute Base

        :param rhs: right hand (value to compare)
        :param opr: operator - one of (<, >, <=, >=, =, !=)
        :param lhs: left hand side (value to check, most likely read from system)
        :return: Compare instance
        '''

        if not isinstance(lhs, Attribute_Base) and not isinstance(rhs, Attribute_Base):
            raise TypeError
        else:
            self.lhs = lhs
            self.rhs = rhs

        if opr not in ['<', '>', '<=', '>=', '!=', '=']:
            raise TypeError
        else:
            if opr is '=':  # set to equivalency python operator
                self.opr = '=='
            else:
                self.opr = opr

        self.deadband = deadband  # deadband applied to rhs of comparison

        self.id = self.lhs.tag+self.opr+self.rhs.tag

        Attribute_Base.__init__(self, self.id)

        self.logger = dlog.MakeChild(self.id)

    def read(self):
        raise NotImplementedError

    def write(self):
        '''Automatically set lhs equal to rhs read value'''
        return self.lhs.write(self.rhs.read()[0])

    def execute(self):
        '''Executes comparison logic'''
        if self.exe_cnt < 1:
            self.start_timer()

        self.exe_cnt += 1

        return self.comp_eval()

    def comp_eval(self):
        '''
        Evaluates comparison:  (rhs) - (lhs) (opr) (deadband)

        Ex. /PI-1875/PV.CV - 65 > 0.1
        '''
        cmp_val = str(self.rhs.read()[0]) +'-'+str(self.lhs.read()[0])+self.opr+str(self.deadband)
        print cmp_val

        self.logger.debug('Evaluating: %s', cmp_val)

        return eval(cmp_val)


# =============================================================
class DiscreteAttribute(Attribute_Base):
    '''Base class for discrete attributes
        Examples:   NamedSets, Binary/Boolean, Bitmask'''
    def __init__(self, tag, attr_path):
        self.tag = tag
        self.attr_path = attr_path
        Attribute_Base.__init__(self, tag, attr_path = attr_path)

    def execute(self, command='compare', op='=', rhs=0):
        if command == 'compare':
            #lhs = Attribute_Base(self.tag, self.attr_path)
            #lhs.set_read_hook(connection.read)
            print "Reading:", self.tag
            readleft = self.read() # this should return theh same value as using OPC_Connect.read(): (0.0, 'Good', <timestamp>)
            if op == '=':
                return readleft[0] == rhs

    # def set_read_hook(self, readhook):
    #     self.lhs.set_read_hook(readhook)
    #     self.rhs.set_read_hook(readhook)
    #
    # def set_write_hook(self, writehook):
    #     self.lhs.set_write_hook(writehook)
    #     self.rhs.set_write_hook(writehook)


class NamedDiscrete(DiscreteAttribute):
    '''Sublcass for attributes with string name mappings to integer values'''
    def __init__(self, tag, int_dict={}, attr_path=''):
        '''

        :param tag:
        :param int_dict:
        :param attr_path:
        :return:
        '''
        self.int_dict = int_dict
        Attribute_Base.__init__(self, tag, attr_path=attr_path)

    def execute(self):
        raise NotImplementedError


class AnalogAttribute(Attribute_Base):
    '''Base class for analog/continuously valued attributes
        Examples: PV, SP, floating point, 16/32 bit integers (ex. modbus values)
    '''
    def execute(self):
        raise NotImplementedError


############################# State Attribute Types (Set Values) ##############################

class ModeAttribute(Attribute_Base):
    '''
    Unique class of attribute for evaluation of DeltaV modes
    '''
    # integer mapping of mode values to MODE.TARGET
    # --> used for writes by default
    target_int_dict = {'LO': 4, 'MAN': 8, 'AUTO': 16, 'CAS': 48, 'ROUT': 144, 'RCAS': 80}

    # integer mapping MODE.ACTUAL (not sure why these are different...)
    # --> used for reads by default
    actual_int_dict = \
        {'LO': 4, 'MAN': 8, 'AUTO': 16, 'CAS': 32, 'ROUT': 128, 'RCAS': 64}

    def __init__(self, tag, attr_path='MODE', **kwargs):
        Attribute_Base.__init__(self, tag, attr_path = attr_path)
        #NamedDiscrete.__init__(self, tag, int_dict=ModeAttribute.target_int_dict, attr_path=attr_path)
        self.target_mode = kwargs.pop('target_mode', '')
        self.tag = tag
        self.attr_path = attr_path

    def setmode(self, mode):
        '''Writes are directed to MODE.TARGET '''
        if type(mode) in [str, unicode]:
            mode = ModeAttribute.target_int_dict[mode]
        return self.write(value=mode, param='TARGET')

    def readmode(self):
        '''Reads are directed to MODE.ACTUAL'''
        return self.read(param='ACTUAL')

    def execute(self, command = 'write'):
        if command == 'write':
            if self.target_mode:
                self.setmode(mode = self.target_mode)
                current_mode = self.readmode()[0]
                return ModeAttribute.actual_int_dict[self.target_mode] == current_mode


class PositionAttribute(ModeAttribute):
    '''
    Unique class of attribute for Valve/Pump position
    '''
    bool_position_dict = {'OPEN': 1, 'CLOSE': 0,
                     'OPENED': 1, 'CLOSED': 0,
                     'START': 1, 'STOP': 0,
                     'RUNNING': 1, 'STOPPED': 0}

    modenum_str_dict = {16: 'AUTO', 32: 'CAS', 48: 'CAS', 128: 'ROUT', 144: 'ROUT', 64: 'RCAS', 80: 'RCAS'}

    # mode:attr_path dictionary --> used for writes by default
    mode_act_dict = {'AUTO': 'SP_D', 'CAS': 'REQ_SP', 'ROUT': 'REQ_OUTP', 'RCAS': 'REQ_SP'}

    # mode: attr_path dictionary--> used for reads by default
    mode_confim_dict = {'AUTO': 'PV_D', 'CAS': 'PV_D', 'ROUT': 'OUTP', 'RCAS': 'PV_D'}

    def __init__(self, tag, attr_path ='', mode_attr=None, **kwargs):
        self.tag = tag
        self.attr_path = attr_path
        self.target_value = kwargs.pop('target_value', None)

        if not mode_attr:
            self.mode = mode_attr
        elif not isinstance(mode_attr, ModeAttribute):
            print "Mode must be a mode attribute type"
            raise TypeError

        ModeAttribute.__init__(self, self.tag)

    def setvalve(self, target_value, **kwargs):
        '''
        :param: target_value can be a boolean number or str(Open/close/start/stop...)
        :param: mode can be int, str or unicode
        '''
        mode = kwargs.pop('mode', '')

        if target_value in [str, unicode]:
            target_value = target_value.upper()
            target_value = PositionAttribute.bool_position_dict[target_value]

        if mode == None:
            mode = self.readmode()[0]

        if type(mode) in [str, unicode]:
            mode = mode.upper()
        elif type(mode) in [int, float]:
            mode = PositionAttribute.modenum_str_dict[mode]

        self.attr_path = PositionAttribute.mode_act_dict[mode]
        return self.write(target_value)

    def readposition(self):
        return self.read()

    def execute(self, command = 'write', **kwargs):
        if command == 'write':
            if self.target_value:
                self.setvalve(self.target_value, mode = self.mode)
                current_value = self.readposition()[0]
                return self.target_value == current_value
            else:
                raise TypeError


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

    def __init__(self, tag, target, message_string, message_path, response_path):
        '''
        :param target: target value of prompt response
        :param message: string of the prompt message
        :return:
        '''
        self.target = target

        self.message_string = message_string

        self.message = Attribute_Base.__init__(self, tag, attr_path=message_path)
        self.response = Attribute_Base.__init__(self,tag, attr_path=response_path)

    def set_read_hook(self, readhook):
        '''Sets readhook for self.message only'''
        self.message.set_read_hook(readhook)

    def set_write_hook(self, writehook):
        '''Sets the writehook for self.response only'''
        self.response.set_write_hook(writehook)

    def write(self, input=None):
        '''
        Writes the target response to the prompt path
        '''

        if input:
            self.response.write(input)
        else:
            self.resonse.write(self.target)

    def read(self):
        '''
        Reads the message string for the prompt
        :return: string of the OAR message
        '''
        read_tup = self.message.read(param='CVS')  # read message string
        if read_tup[1] == "Good":
            return read_tup[0]
        else:
            # bad read value, problem with path string or client
            raise IOError

    def execute(self):
        '''Reads prompt message, checking against message string'''
        message_value = self.read()

        if message_value == self.message_string:
            self.set_complete(True)

    def force(self, value=None):
        '''Write prompt response self.target'''
        if self.value:
            self.write(input=value)
        else:  # write self.target to response path
            self.write()

class InicationAttribute(Attribute_Base):
    '''
    Unique class of attribute for PV indication.
    Ex: Flow Rate (FIC), Tank Level, PH, Pressure (PIC), Temperature (TI), Tank Weight, etc.
    Indicators use AI1 or INT1 functional blocks
    '''

    def __init__(self, tag, attr_path):
        self.tag = tag
        self.attr_path = attr_path
        Attribute_Base.__init__(self, tag, attr_path = attr_path)

    def read(self):
        Attribute_Base(self.tag, self.attr_path).read()

    def execute(self, command = 'read'):
        if command == 'read':
            if (self.read()[0]) and (self.read()[1] == 'Good'):
                return True
            else:
                return False


class LoopAttribute(Attribute_Base):
    '''
    Attribute for handling feedback controls.
    Includes:
        indicator attribute for field value
        analog attribute for setpoint
        position attribute for actuator position
    '''
    def __init__(self, tag, indicator, setpoint, position):
        '''
        :param tag:
        :param indicator: attribute type for process value
        :param setpoint: attribute type for setpoint
        :param position: attribute type for final control
        :return:
        '''
        for sub_attr in [indicator, setpoint, position]:
            if not isinstance(sub_attr, Attribute_Base):
                raise TypeError

        self.pv = indicator
        self.sp = setpoint
        self.out = position
        Attribute_Base.__init__(self, tag)

    def execute(self):
        '''verify a match between indicator value and setpoint'''
        pass

    def force(self):
        '''sets the vavle position in manual'''
        pass

class EMCMDAttribute(Attribute_Base):
    #TODO: import EMCMD dictionary to EMCMD_int_dict
    EMCMD_int_dict = {}

    def __int__(self, tag, attr_path = ''):
        ''' :param: tag: the name of EM class
        '''
        self.attr_path = attr_path
        self.tag = tag
        Attribute_Base.__init__(self, tag, attr_path=self.attr_path)

    def write(self, target):
        self.attr_path = 'A_COMMAND'
        self.target = target
        if target in [str, unicode]:
            self.target = EMCMDAttribute.EMCMD_int_dict[target]
        return Attribute_Base(tag = self.tag, attr_path = self.attr_path).write(self.target)

    def readtarget(self):
        self.attr_path = 'A_TARGET'
        return Attribute_Base(tag = self.tag, attr_path = self.attr_path).read()

    def readPV(self):
        self.attr_path = 'A_PV'
        return Attribute_Base(tag = self.tag, attr_path = self.attr_path).read()

    def execute(self, command = 'write', **kwargs):
        if command == 'write':
            target = kwargs.pop('target', '')
            self.write(target)
            readtarget = self.readtarget()[0]
            readPV = self.readPV()[0]
            #TODO: confirm below:
            return readtarget == self.target or readPV == self.target


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
        return Attribute_Base.read(self, param = self.param)

    def write(self, target_value):
        return Attribute_Base.write(self, value = target_value, param = self.param)

    def execute(self, command = 'read', **kwargs):
        if command == 'read':
            if (self.read()[0]) and (self.read()[1] == 'Good'):
                return True
            else:
                return False
        elif command == 'write':
            target_value = kwargs.pop('target_value', '')
            if target_value:
                self.write(target_value)
                current_value = self.read()[0]
                return target_value == current_value
            else:
                raise TypeError

class AttributeDummy(Attribute_Base):
    def __init__(self):
        Attribute_Base.__init__(self, tag = '')

    def read(self):
        pass

    def write(self):
        pass

    def execute(self):
        pass

#####################Transition Attribute Types (use read functions and compare) #########################
class ComparisonAttributes(object):

    operator_dict = {'>': operator.gt,
                     '>=': operator.ge,
                     '==': operator.eq,
                     '=': operator.eq,
                     '<': operator.lt,
                     '<=': operator.le,
                     '!=': operator.ne}

    #TODO: Get system values with the read functions above
    def __init__(self, **kwargs):
        # just a string
        self.op = kwargs.pop('op', '')
        self.lhs = kwargs.pop('lhs', AttributeDummy())
        self.rhs = kwargs.pop('rhs', AttributeDummy())

    def execute(self, **kwargs):
        if self.op not in ComparisonAttributes.operator_dict:
            raise TypeError

        leftval = self.lhs.read()[0]  # this should return the same value as using OPC_Connect.read(): (0.0, 'Good', <timestamp>)
        rightval = self.rhs.read()[0]
        op = ComparisonAttributes.operator_dict[self.op]
        return op(leftval, rightval)

    def set_read_hook(self, readhook):
        self.lhs.set_read_hook(readhook)
        self.rhs.set_read_hook(readhook)

    def set_write_hook(self, writehook):
        self.lhs.set_write_hook(writehook)
        self.rhs.set_write_hook(writehook)


if __name__ == "__main__":
    from tools.serverside.OPCclient import OPC_Connect

    connection = OPC_Connect()

    m1 = ModeAttribute('CV-1423', 'DC1/MODE')
    m2 = ModeAttribute('CV-3854', 'MODE')

    attrs = [m1, m2]

    for attr in attrs:
        attr.set_read_hook(connection.read)
        attr.set_write_hook(connection.write)
