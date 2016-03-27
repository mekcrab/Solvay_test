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

dlog = LogTools('AttributeTypes.log', config.log_level, 'AttributeTypes')
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

        self._default_test = None  # function hook to set default testing behavior of execute

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

    def _read(self, param='CV'):
        '''Stub for reading a value for this attribute
        Set instance attribute self.readhook in subclasses or at runtime via self.set_read_hook.
        :return: value read from system.'''
        read_path = self.OPC_path() + '.' + param
        return self.readhook(read_path)

    def set_read_hook(self, readhook):
        self.readhook = readhook

    def _write(self, target_value, param='CV'):
        '''Stub for writing to this attribute's value.
        :return: sucess of write'''
        write_path = self.OPC_path() + '.' + param
        return self.writehook(write_path, target_value)

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
        self.data.append((time.time(), self._read()))

# =============================================================
class DiscreteAttribute(Attribute_Base):
    '''
    Base class for discrete attributes
    Examples:   NamedSets, Binary/Boolean, Bitmask
    '''

    def __init__(self, tag, attr_path, target_value=0):
        self.tag = tag
        self.attr_path = attr_path
        self.target_value = target_value
        Attribute_Base.__init__(self, tag, attr_path=attr_path)

    def execute(self, command='compare', op='=', target_value=0):
        if command == 'compare':
            print "Reading:", self.tag
            readleft = self._read() # this should return the same value as using OPC_Connect.read(): (0.0, 'Good', <timestamp>)
            if op == '=':
                return readleft[0] == target_value

    def force(self, target_value=1):
        '''Attempts to force the value of this attribute'''
        return self._write(target_value)

    # def set_read_hook(self, readhook):
    #     self.lhs.set_read_hook(readhook)
    #     self.rhs.set_read_hook(readhook)
    #
    # def set_write_hook(self, writehook):
    #     self.lhs.set_write_hook(writehook)
    #     self.rhs.set_write_hook(writehook)


class NamedDiscrete(DiscreteAttribute):
    '''Sublcass for attributes with string name mappings to integer values'''
    def __init__(self, tag, int_dict={}, attr_path='', target_value=0):
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
    '''
    Base class for analog/continuously valued attributes
    Examples: PV, SP, floating point, 16/32 bit integers (ex. modbus values)
    '''
    def __init__(self):
        raise NotImplementedError


############################# State Attribute Types (Set Values) ##############################

class Constant(Attribute_Base):
    '''Attribute wrapper for constant values like numbers, strings, etc'''

    def __init__(self, target_value, *args, **kwargs):

        if type(target_value) in [int, float, str, unicode]:
            self.val = target_value
        else:
            raise TypeError
        Attribute_Base.__init__(self, 'Constant', path=target_value)

    def read(self):
        return (self.val, 'Good', time.ctime())

    def write(self, target_value):
        self.val = target_value
        return 'Success'

    def execute(self, command = 'write'):
        if command == 'write':
            self.write(self.val)
            return True
        elif command == 'read':
            return self.read()[0]

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
        #NamedDiscrete.__init__(self, tag, int_dict=ModeAttribute.target_int_dict, attr_path=attr_path)
        self.target_value = kwargs.pop('target_value', '')
        self.tag = tag
        self.attr_path = attr_path
        Attribute_Base.__init__(self, self.tag, attr_path = attr_path)

    def write_Mode(self, target_value):
        '''Writes are directed to MODE.TARGET '''
        if type(target_value) in [str, unicode]:
            target_value = ModeAttribute.target_int_dict[target_value]
        return self._write(target_value=target_value, param='TARGET')

    def read_Mode(self):
        '''Reads are directed to MODE.ACTUAL'''
        return self._read(param='ACTUAL')

    def write(self, target_value):
        return self.write_Mode(target_value=target_value)

    def read(self):
        return self.read_Mode()

    def execute(self, command = 'write'):
        if command == 'write':
            if self.target_value:
                self.write(target_value= self.target_value)
                current_mode = self.read()[0]
                return ModeAttribute.actual_int_dict[self.target_value] == current_mode
        elif command == 'read':
            return self.read()[0]


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
            self.mode = kwargs.pop('mode', None)
        elif not isinstance(mode_attr, ModeAttribute):
            print "Mode must be a mode attribute type"
            raise TypeError

        ModeAttribute.__init__(self, self.tag)

    def write(self, target_value, **kwargs):
        '''
        :param: target_value can be a boolean number or str(Open/close/start/stop...)
        :param: mode can be int, str or unicode
        '''
        mode = kwargs.pop('mode', '')

        if target_value in [str, unicode]:
            target_value = target_value.upper()
            target_value = PositionAttribute.bool_position_dict[target_value]

        if mode != None:
            self.write_Mode(target_value=mode)
        else:
            mode = self.read_Mode()[0]

        if type(mode) in [str, unicode]:
            mode = mode.upper()
        elif type(mode) in [int, float]:
            mode = PositionAttribute.modenum_str_dict[mode]

        self.attr_path = PositionAttribute.mode_act_dict[mode]
        return self._write(target_value)

    def read(self):
        return self._read()

    def execute(self, command = 'write'):
        if command == 'write':
            if self.target_value != None:
                self.write(self.target_value, mode = self.mode)
                current_value = self.read()[0]
                return self.target_value == current_value
            else:
                raise TypeError
        elif command == 'read':
            mode = PositionAttribute.modenum_str_dict[self.read_Mode()[0]]
            self.attr_path = PositionAttribute.mode_act_dict[mode]
            return self.read()[0]


class InterlockAttribute(Attribute_Base):
    '''Interlock trip/resets in devices'''
    # TODO: extend class to cover interlock masters
    def __init__(self, tag, test_param='trip', **kwargs):
        '''
        Constructor
        :param tag: Device tag
        :param condition_no: condition number
        :return:
        '''
        self.condition = kwargs.pop('condition', None)

        if self.condition:
            self.trip = DiscreteAttribute(tag, 'INTERLOCK/CND'+str(self.condition))
        else:
            self.trip = DiscreteAttribute(tag, '/INTERLOCK/INTERLOCK')
        self.reset = DiscreteAttribute(tag, 'INTERLOCK/RESET_D')
        self.bypass = DiscreteAttribute(tag, 'INTERLOCK/BYPASS_ILK')
        Attribute_Base.__init__(self, tag)

        self.set_test_param(test_param)

    def set_test_param(self, param):
        '''
        Method hook for the interlock attribute instance
        :param self:
        :param param: name of param to test
        :return:
        '''
        valid_params = {
            'trip': self.test_trip,
            'reset': self.test_reset,
            'test_bypass': self.test_bypass
        }
        self._default_test = valid_params[param]

    def test_trip(self):
        '''
        Tests if interlock is tripped
        :param
        :return:
        '''
        return self.trip.execute(target_value=1)

    def test_reset(self):
        '''
        Tests if interlock is reset
        :param self:
        :return:
        '''
        return self.reset.execute(target_value=1)

    def test_bypass(self):
        '''
        Tests if interlock is bypassed
        :param self:
        :return:
        '''
        return self.bypass.execute(target_value=1)

    def execute(self):
        '''
        Checks specified parameter specified
        :param test_param: name of parameters to test
        :return:
        '''
        return self._default_test()

    def force(self, param='reset'):
        '''
        Force reset or bypass of interlock.
        :param self:
        :return:
        '''
        # TODO: think of a more explicit way to make this flexible and dynamic based on embedded attributes
        return getattr(self, param).force()

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

    def __init__(self, tag, target_value, message_string, message_path, response_path):
        '''
        :param target_value: target value of prompt response
        :param message: string of the prompt message
        :return:
        '''
        self.target = target_value

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
            self.response._write(input)
        else:
            self.response._write(self.target)

    def read(self):
        '''
        Reads the message string for the prompt
        :return: string of the OAR message
        '''
        read_tup = self.message._read(param='CVS')  # read message string
        if read_tup[1] == "Good":
            return read_tup[0]
        else:
            # bad read value, problem with path string or client
            raise IOError

    def execute(self, command = 'write'):
        '''Reads prompt message, checking against message string'''
        if command == 'write':
            message_value = self.read()

            if message_value == self.message_string:
                self.set_complete(True)

        if command == 'read':
            return self.response._read()

    def force(self, value=None):
        '''Write prompt response self.target'''
        self.value = value
        if self.value:
            self.write(input=value)
        else:  # write self.target to response path
            self.write()


class IndicationAttribute(Attribute_Base):
    '''
    Unique class of attribute for PV indication.
    Ex: Flow Rate (FIC), Tank Level, PH, Pressure (PIC), Temperature (TI), Tank Weight, etc.
    Indicators use AI1 or INT1 functional blocks
    '''

    def __init__(self, tag, attr_path = 'PV'):
        self.tag = tag
        self.attr_path = attr_path
        Attribute_Base.__init__(self, tag, attr_path=attr_path)

    def read(self):
        return self._read()

    def execute(self, command = 'write'):
        if command == 'write':
            if (self.read()[0]) and (self.read()[1] == 'Good'):
                return True
            else:
                return False
        if command == 'read':
            return self.read()[0]

    def force(self):
        '''
        Force a simulation value for this indicator
        either through MiMiC or DeltaV simulate parameters
        '''
        raise NotImplementedError


class LoopAttribute(Attribute_Base):
    '''
    Attribute for handling feedback controls.
    Includes:
        indicator attribute for field value
        analog attribute for setpoint
        position attribute for actuator position
    '''
    def __init__(self, tag, indicator, target_value, position):
        '''
        :param tag:
        :param indicator: attribute type for process value
        :param target_value: attribute type for setpoint
        :param position: attribute type for final control
        :return:
        '''
        for sub_attr in [indicator, target_value, position]:
            if not isinstance(sub_attr, Attribute_Base):
                raise TypeError

        self.pv = indicator
        self.sp = target_value
        self.out = position
        Attribute_Base.__init__(self, tag)

    def execute(self):
        '''
        verify a match between indicator value and setpoint
        '''
        pass

    def force(self):
        '''
        Sets the valve position in manual
        '''
        pass


class EMCMDAttribute(Attribute_Base):
    # TODO: import EMCMD dictionary to EMCMD_int_dict
    # could this attribute type just be a NamedDiscrete with the correct
    # command integer value for a self.force(target)?
    EMCMD_int_dict = {}

    def __int__(self, tag, attr_path = '', **kwargs):
        ''' :param: tag: the name of EM class
        '''
        self.attr_path = attr_path
        self.tag = tag
        self.target_value = kwargs.pop('target_value', '')
        Attribute_Base.__init__(self, tag, attr_path=self.attr_path)

    def write(self):
        self.attr_path = 'A_COMMAND'
        if self.target_value in [str, unicode]:
            self.target_value = EMCMDAttribute.EMCMD_int_dict[self.target_value]
        return self._write(self.target_value)

    def read(self):
        return self.read_PV()

    def read_Target(self):
        self.attr_path = 'A_TARGET'
        return self._read()

    def read_PV(self):
        self.attr_path = 'A_PV'
        return self._read()

    def execute(self, command = 'write'):
        if command == 'write':
            self.write()
            readtarget = self.read_Target()[0]
            readPV = self.read_PV()[0]
            #TODO: confirm below:
            return readtarget == self.target_value or readPV == self.target_value
        if command == 'read':
            return self.read()[0]


class PhaseCMDAttribute(NamedDiscrete):
    #TODO: import Phase Command dictionary to PhaseCMD_int_dict
    #TODO: Which attr_path are we using to run a phase??? - XCOMMAND
    #TODO:      --> However the phase will need to be loaded to a given unit before execution

    def __int__(self):
        pass


class OtherAttribute(Attribute_Base):
    '''
    Catch-all class for other attributes, based on absolute OPC path
    '''
    def __init__(self, tag, attr_path, param = 'CV', **kwargs):
        self.param = param
        self.target_value = kwargs.pop('target_value',None)
        Attribute_Base.__init__(self, tag, attr_path=attr_path)

    def read(self):
        return self._read(param = self.param)

    def write(self, target_value):
        return self._write(target_value= target_value, param = self.param)

    def execute(self, command = 'write', **kwargs):
        if command == 'read':
            return self.read()[0]
        elif command == 'write':
            if self.target_value:
                self.write(self.target_value)
                current_value = self.read()[0]
                return self.target_value == current_value
            else:
                raise TypeError

class AttributeDummy(Attribute_Base):
    '''
    Dummy attribute for:
        testing, as a placeholder, or deferring attributes type differentiation'''

    def __init__(self, id=''):
        '''Constructor'''
        self.id = id
        Attribute_Base.__init__(self, tag='dummy')

    def read(self):
        print 'Dummy read ', self.id

    def write(self, target_value=0):
        print 'Dummy write', self.id, 'as ', target_value

    def execute(self):
        if not self.complete:
            self.set_complete(True)
            self.deactivate()
        else:
            pass

    def force(self):
        print 'Dummy force'


class Calculate(Attribute_Base):
    def __init__(self, lhs = AttributeDummy(), op = '', rhs = AttributeDummy()):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op
        self.id = self.lhs.tag + self.op + self.rhs.tag
        Attribute_Base.__init__(self, self.id)

        operator_list = ['+', '-', '*', '/', '**']

        if self.op not in operator_list:
            raise TypeError
        else:
            self.leftval = self.lhs.execute(command='read')
            self.rightval = self.rhs.execute(command='read')

    def calc(self):
        return eval(''.join(['float(%r)'%self.leftval , self.op, 'float(%r)'%self.rightval]))

    def write(self):
        raise NotImplementedError

    def read(self):
        return self.calc()

    def execute(self, command='write'):
        if command == 'write':
            return self.write()
        if command == 'read':
            return self.read()


#####################Transition Attribute Types (use read functions and compare) #########################
class Compare(Attribute_Base):

    operator_dict = {'>': operator.gt,
                     '>=': operator.ge,
                     '==': operator.eq,
                     '=': operator.eq,
                     '<': operator.lt,
                     '<=': operator.le,
                     '!=': operator.ne}

    def __init__(self, lhs=AttributeDummy(), op='', rhs=AttributeDummy(), deadband=0):
        '''
        Comparison between two sub-attributes in the form of:
            (left hand side) (operator) (right hand side)
        Ex: PI-1783 > 65
        Both rhs and lhs must be sub classes of Attribute Base
        :param rhs: right hand (value to compare)
        :param opr: operator - one of (<, >, <=, >=, =, !=)
        :param lhs: left hand side (value to check, most likely read from system)
        :param deadband: tolerance of comparison value
        :return: Compare instance
        '''

        if op not in Compare.operator_dict:
            self.logger.error("Comparison operator \"%s\" not valid", op)
            raise NameError
        else:
            self.op = op

        if isinstance(lhs, Attribute_Base) and isinstance(rhs, Attribute_Base):
            self.lhs = lhs
            self.rhs = rhs
        else:
            raise TypeError

        self.deadband = deadband  # deadband applied to rhs of comparison

        self.id = self.lhs.tag+self.op+self.rhs.tag

        self.logger = dlog.MakeChild(self.id)

        Attribute_Base.__init__(self, self.lhs.tag)

    def read(self):
        raise NotImplementedError

    def write(self):
        return self.lhs._write(target_value=self.rhs.read()[0])

    def comp_eval(self):
        '''
        Evaluates comparison:  (lhs) - (rhs) (opr) (deadband)
        Ex. /PI-1875/PV.CV - 65 > 0.1
        '''
        self.leftval = self.lhs.execute(command='read')
        self.rightval = self.rhs.execute(command='read')
        cmp_val = str(self.leftval) +'-'+str(self.rightval)+self.op+str(self.deadband)

        self.logger.debug('Evaluating: %s', cmp_val)

        return eval(cmp_val)

        # op = ComparisonAttributes.operator_dict[self.op]
        # return op(self.leftval, self.rightval)

    def set_read_hook(self, readhook):
        self.lhs.set_read_hook(readhook)
        self.rhs.set_read_hook(readhook)

    def set_write_hook(self, writehook):
        self.lhs.set_write_hook(writehook)
        self.rhs.set_write_hook(writehook)

    def execute(self):
        if self.exe_cnt < 1:
            self.start_timer()

        self.exe_cnt += 1

        if self.comp_eval():
            self.set_complete()
        else:
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
