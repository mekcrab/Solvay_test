'''Module contains class definitions for attributes to be executed on the runtime system'''

from AttributeBase import AttributeBase, AttributeDummy
import operator

from tools.Utilities.Logger import LogTools
dlog = LogTools('AttributeTypes.log', 'ExecutionAttributes')
dlog.rootlog.warning('ExecutionAttributes initialized')


class DiscreteAttribute(AttributeBase):
    '''
    Base class for discrete attributes
    Examples:   NamedSets, Binary/Boolean, Bitmask
    '''

    def __init__(self, tag, attr_path, target_value=0, **kwargs):
        self.tag = tag
        self.attr_path = attr_path
        self.target_value = target_value
        AttributeBase.__init__(self, tag, attr_path=attr_path, **kwargs)

    def read(self, param='CV'):
        self.last_read = self._read(param=param)
        self.logger.info('Read: %s', self.last_read)
        return self.last_read[0]

    def write(self, target_value, param='CV'):
        val = self._write(target_value, param=param)
        self.logger.info('Write %s: %s', val, target_value)
        return val

    def check_status(self):
        return self._read(param='ST')[0]

    def check_value(self):
        '''
        Tests to see if the current value of this attribute equal self.target_value.
        Sets self.complete as required
        '''
        if self.read() == self.target_value:
            return self.set_complete(True)
        else:
            return self.set_complete(False)

    def force(self, target_value=None):
        '''
        Attempts to force the value of this attribute to the specified target_value.
        Defaults to self.target_value. Once successful reset execute method to verify target.
        '''
        if not target_value:
            target_value = self.target_value

        return self.write(target_value)


class NamedDiscrete(DiscreteAttribute):
    '''Sublcass for attributes with string name mappings to integer values'''
    def __init__(self, tag, attr_path='', **kwargs):
        '''
        Constructor
        '''
        self.namedset_dict = kwargs.pop('namedset_dict', {'default':0})

        self.target_name = kwargs.pop('target_name', 'default')
        if 'target_value' not in kwargs:
            kwargs['target_value'] = self.namedset_dict[self.target_name]

        AttributeBase.__init__(self, tag, attr_path=attr_path, **kwargs)

    def set_target_value(self, target_value):
        if type(target_value) in [str, unicode]:
            self.target_name = target_value
            self.target_value = self.namedset_dict[self.target_name]
        elif type(target_value) is int:
            self.target_value = target_value
        else:
            raise TypeError

    def get_name_value(self, name=None):
        if name:
            name = self.target_name
        return self.namedset_dict[name]


class ModeAttribute(AttributeBase):
    '''
    Unique class of attribute for evaluation of DeltaV modes.

    Composite of two NamedDiscrete attributes: self.actual_mode for mode.actual, self.target_mode for mode.target
         (don't confuse mode.target for target_value and target_n
    '''
    # integer mapping of mode values to MODE.TARGET
    # --> used for writes by default
    target_int_dict = {'LO': 4, 'MAN': 8, 'AUTO': 16, 'CAS': 48, 'ROUT': 144, 'RCAS': 80}

    # integer mapping MODE.ACTUAL (not sure why these are different...)
    # --> used for reads by default
    actual_int_dict = \
        {'LO': 4, 'MAN': 8, 'AUTO': 16, 'CAS': 32, 'ROUT': 128, 'RCAS': 64}

    def __init__(self, tag, attr_path='MODE', **kwargs):
        if 'target_name' in kwargs:
            mode_string = kwargs.pop('target_name', 'CAS')
        elif 'target_mode' in kwargs:
            mode_string = kwargs.pop('target_mode', 'CAS')
        elif 'target_value' in kwargs:
            mode_string = kwargs.pop('target_value', 'CAS')

        self.mode_name = mode_string

        self.target_mode = NamedDiscrete(tag, attr_path=attr_path+'.TARGET',
                                         namedset_dict=ModeAttribute.target_int_dict,
                                         target_name=mode_string)
        self.actual_mode = NamedDiscrete(tag, attr_path=attr_path+'.ACTUAL',
                                         namedset_dict=ModeAttribute.actual_int_dict,
                                         target_name=mode_string)

        AttributeBase.__init__(self, tag, attr_path=attr_path, **kwargs)

    def set_target_value(self, target_value):
        '''Sets test targets for both target_mode and actual_mode'''
        self.target_mode.set_target_value(target_value)
        self.actual_mode.set_target_value(target_value)

    def set_read_hook(self, readhook):
        self.target_mode.set_read_hook(readhook)
        self.actual_mode.set_read_hook(readhook)

    def set_write_hook(self, writehook):
        self.target_mode.set_write_hook(writehook)
        self.actual_mode.set_write_hook(writehook)

    @staticmethod
    def get_mode_target(mode_str):
        '''Returns integer value of mode target given by mode_str'''
        return ModeAttribute.target_int_dict[mode_str]

    @staticmethod
    def get_mode_actual(mode_str):
        '''Returns integer value of mode actual given by mode_str'''
        return ModeAttribute.actual_int_dict[mode_str]

    def write_mode(self, mode_value):
        '''Writes are directed to MODE.TARGET '''
        if type(mode_value) in [str, unicode]:
            mode_int = self.get_mode_target(mode_value)
        elif type(mode_value) in [int, float]:
            mode_int = int(mode_value)
        else:
            print "Mode types must be string or integers"
            raise
        return self.target_mode.write(value=mode_int, param='TARGET')

    def write(self, mode):
        return self.write_mode(mode_value=mode)

    def read_mode(self):
        '''Reads are directed to MODE.ACTUAL'''
        return self.actual_mode.read(param='ACTUAL')

    def read(self):
        self.last_read = self.read_mode()
        return self.laster_read

    def check_value(self):
        if self.read() == self.get_mode_actual(self.mode_name):
            return self.set_complete(True)
        else:
            return self.set_complete(False)

    def force(self):
        return self.write_mode(self.get_mode_target(self.mode_name))


class PositionAttribute(AttributeBase):
    '''
    Unique class of attribute for Valve/Pump position. Includes mode checking in self.mode embedded attribute
    '''
    bool_position_dict = {'OPEN': 1, 'CLOSE': 0,
                          'OPENED': 1, 'CLOSED': 0,
                          'START': 1, 'STOP': 0,
                          'RUNNING': 1, 'STOPPED': 0}

    # mode:attr_path dictionary --> used for writes by default
    mode_sp_dict = {'AUTO': 'SP_D', 'CAS': 'REQ_SP', 'ROUT': 'REQ_OUTP', 'RCAS': 'REQ_SP'}

    # mode: attr_path dictionary--> used for reads by default
    mode_pv_dict = {'AUTO': 'PV_D', 'CAS': 'PV_D', 'ROUT': 'OUT', 'RCAS': 'PV_D',
                    16: 'PV_D', 32: 'PV_D', 128: 'OUT', 64: 'PV_D'}

    def __init__(self, tag, attr_path='PV_D', target_mode='CAS', **kwargs):

        self.target_value = kwargs.pop('target_value', None)
        self.attr_path = attr_path

        # sp_path, pv_path are dynamically connected based on self.mode.mode_name if not specified
        self.write_path = kwargs.pop('sp_path', None)
        self.read_path = kwargs.pop('pv_path', None)

        mode_path = kwargs.pop('mode_path', 'MODE')
        self.mode = ModeAttribute(tag, attr_path=mode_path, target_mode=target_mode)

        AttributeBase.__init__(self, tag, attr_path=self.attr_path, target_value=self.target_value, **kwargs)

    def set_read_hook(self, readhook):
        AttributeBase.set_read_hook(self, readhook)
        self.mode.set_read_hook(readhook)

    def set_write_hook(self, writehook):
        AttributeBase.set_write_hook(self, writehook)
        self.mode.set_write_hook(writehook)

    def write(self, target_value=None):
        '''
        Writes target value to the appropriate setpoint based on current mode
        :param: target_value: can be a boolean number or str(Open/close/start/stop...)
        '''
        # target_value must be an interger or floating point to write
        if target_value == None:
            target_value = self.target_value
        elif target_value in [str, unicode]:
            target_value = target_value.upper()
            if target_value in PositionAttribute.bool_position_dict:
                target_value = PositionAttribute.bool_position_dict[target_value]
            else:  # attempt to convert from string type to floating point
                target_value = float(target_value)
        elif type(target_value) in [int, float]:
            pass
        else:
            raise TypeError

        # write to target mode
        self.write_mode()

        # determine the correct parameter to write based on mode
        if not self.write_path:
            self.attr_path = PositionAttribute.mode_sp_dict[self.mode.mode_name]
        return self._write(target_value)

    def read(self, param='CV'):
        if not self.read_path:
            if self.read_mode() in PositionAttribute.mode_pv_dict:
                self.attr_path = PositionAttribute.mode_pv_dict[self.read_mode()]
        self.last_read = self._read(param=param)

    def write_mode(self, target_mode=None):
        '''Wrapper to write this position's mode attribute, defaults to required mode'''
        if not target_mode:
            target_mode = self.mode.mode_name

        return self.mode.write(target_mode)

    def read_mode(self):
        '''Wrappper to read from this position's mode attribute'''
        return self.mode.read()

    def check_mode(self):
        '''Wrapper to self.mode.check_mode'''
        check = self.mode.check_value()
        if check:
            pass
        else:
            self.logger.warning('Mode target/actual mismatch: %s/%s ',
                                self.mode.target.last_read[0], self.mode.actual.last_read[0])
        return check

    def check_value(self):
        self.last_read = self.read()
        if self.last_read == self.target_value:
            return self.set_complete(True)
        else:
            return self.set_complete(False)

    def force(self, target_value=None):
        '''Forces target mode and writes to appropriate SP'''
        if not target_value:
            target_value = self.target_value

        self.logger.debug('Forcing position to (%s) in mode: %s', target_value, self.target_mode)

        return self.write(target_value)


class InterlockAttribute(AttributeBase):
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
        self.attr_path = ''

        if self.condition:
            self.trip = DiscreteAttribute(tag, 'INTERLOCK/CND'+str(self.condition))
        else:
            self.trip = DiscreteAttribute(tag, '/INTERLOCK/INTERLOCK', target_value=1)
        self.reset = DiscreteAttribute(tag, 'INTERLOCK/RESET_D', target_value=1)
        self.bypass = DiscreteAttribute(tag, 'INTERLOCK/BYPASS_ILK', target_value=1)
        AttributeBase.__init__(self, tag)

        self.set_test_param(test_param)

    def set_test_param(self, param):
        '''
        Sets execute method hook to the
        :param self:
        :param param: name of param to test
        :return:
        '''
        valid_params = {
            'trip': self.check_trip,
            'reset': self.check_reset,
            'test_bypass': self.check_bypass
        }
        if param not in valid_params:
            raise NameError
        else:
            self.set_execute(valid_params[param]())

    def check_trip(self):
        '''
        Tests if interlock is tripped
        :param
        :return:
        '''
        return self.trip.execute()

    def check_reset(self):
        '''
        Tests if interlock requires a reset
        :param self:
        :return:
        '''
        return self.reset.execute()

    def check_bypass(self):
        '''
        Tests if interlock is bypassed
        :param self:
        :return:
        '''
        return self.bypass.execute()

    def check_value(self):
        '''
        Checks if the interlock is active and not bypassed
        :param test_param: name of parameters to test
        :return:
        '''
        if self.check_trip() and not self.check_bypass():
            return self.set_complete(True)
        else:
            return self.set_complete(False)

    def ilk_reset(self):
        '''
        Resets interlock trip
        :return:
        '''
        return self.reset.force(target_value=1)

    def ilk_bypass(self):
        return self.bypass.force(target_value=1)

    def force(self):
        '''
        Force bypass of an interlock.
        :param self:
        :return:
        '''
        if not self.check_bypass():
            return self.ilk_bypass()
        else:
            return True


class PromptAttribute(AttributeBase):
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
        :param target_value: target value of prompt response - can be an attribute that requires action!!
        :param message: string of the prompt message
        :return:
        '''

        self.message_string = message_string

        self.message = AttributeBase.__init__(self, tag, attr_path=message_path)

        if isinstance(target_value, AttributeBase):  # operator action required via target_value.force() method
            self.response = target_value
        else:
            self.response = AttributeBase(tag, attr_path=response_path, target_value=target_value)

        self.target_value = self.response.target_value

    def set_read_hook(self, readhook):
        '''Sets readhook for self.message and self.response'''
        self.message.set_read_hook(readhook)
        self.response.set_read_hook(readhook)

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
            self.response._write(self.target_value)

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

    def check_value(self):
        '''Reads prompt message, checking against message string'''
        message_value = self.read()

        if message_value == self.message_string:
            return self.set_complete(True)
        else:
            return self.set_complete(False)

    def force(self, value=None):
        '''Write prompt response self.target'''
        if self.response.check_value():
            self.logger.warning('Response %s already set to target %s', self.response.last_read, self.target_value)

        self.logger.debug('OAR response %s to %r', self.target_value, self.response)
        return self.response.force()


class AnalogAttribute(AttributeBase):
    '''
    Base class for analog/continuously valued attributes
    Examples: PV, SP, floating point, 16/32 bit integers (ex. modbus values), analog valve position outputs
    '''
    def __init__(self, tag, **kwargs):
        AttributeBase.__init__(self, tag, **kwargs)

    def read(self):
        self.last_read = self._read()
        self.logger.info("Read: %s". self.last_read)
        return self.last_read[0]

    def write(self, target_value=None):
        if not target_value:
            if self.target_value:
                target_value = self.target_value
            else:
                self.logger.error("No target value specified for %r", self)
                raise AttributeError

        self.logger.info("Writing %s to %s", target_value, self.OPC_path())
        return self._write(target_value)


class IndicationAttribute(AnalogAttribute):
    '''
    Unique class of attribute for PV indication.
    Ex: Flow Rate (FIC), Tank Level, PH, Pressure (PIC), Temperature (TI), Tank Weight, etc.
    Indicators use AI1 or INT1 functional blocks
    '''

    def __init__(self, tag, attr_path = 'PV', target_value=0, **kwargs):
        self.tag = tag
        self.attr_path = attr_path
        self.target_value = target_value
        AttributeBase.__init__(self, tag, attr_path=attr_path, **kwargs)

    def force(self):
        '''
        Force a simulation value for this indicator
        either through MiMiC or DeltaV simulate parameters -
        saved for future work as it may require a separate OPC client for the writehook
        '''
        raise NotImplementedError


class LoopAttribute(AttributeBase):
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
            if not isinstance(sub_attr, AttributeBase):
                raise TypeError

        self.pv = indicator
        self.sp = setpoint
        self.out = position
        self.target_value = self.sp.target_value
        AttributeBase.__init__(self, tag)

    def check_value(self):
        '''
        verify a match between indicator value and setpoint
        '''
        self.pv.set_target_value(self.target_value)
        if self.pv.check_value():
            self.set_complete(True)
        else:
            self.set_complete(False)

    def force(self):
        '''
        Sets the valve position in manual
        '''
        raise NotImplementedError


class OtherAttribute(AttributeBase):
    '''
    Catch-all class for other attributes, based on absolute OPC path
    '''
    def __init__(self, tag, attr_path, param = 'CV', **kwargs):
        self.param = param
        self.target_value = kwargs.pop('target_value',None)
        AttributeBase.__init__(self, tag, attr_path=attr_path, **kwargs)

    def read(self):
        return self._read(param=self.param)[0]

    def write(self, target_value=None):
        if not target_value:
            target_value = self.target_value

        return self._write(value=target_value, param=self.param)

    def execute(self, command = 'write', **kwargs):
        if not self.exe_start:
            self.start_timer()

        val = self.read()
        if val == self.target_value:
            return self.set_complete(True)
        else:
            return self.set_complete(False)


class EMCMDAttribute(AttributeBase):
    # TODO: import EMCMD dictionary to EMCMD_int_dict
    # could this attribute type just be a NamedDiscrete with the correct
    # command integer value for a self.force(target_value)?
    EMCMD_int_dict = {}

    def __int__(self, tag, attr_path = '', **kwargs):
        ''' :param: tag: the name of EM class
        '''
        self.attr_path = attr_path
        self.tag = tag
        self.target_value = kwargs.pop('target_value', '')
        AttributeBase.__init__(self, tag, attr_path=self.attr_path, **kwargs)

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
        raise NotImplementedError


class Calculate(AttributeBase):
    def __init__(self, lhs = AttributeDummy(), op = '', rhs = AttributeDummy(), **kwargs):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op
        self.id = self.lhs.tag + self.op + self.rhs.tag
        AttributeBase.__init__(self, self.id, **kwargs)

        operator_list = ['+', '-', '*', '/', '**']

        if self.op not in operator_list:
            self.logger.error('Undefined operator: %s', self.op)
            raise TypeError

        self.leftval = self.lhs.last_read
        self.rightval = self.rhs.last_read

    def calc(self):
        return eval(''.join(['float(%r)'%self.leftval , self.op, 'float(%r)'%self.rightval]))

    def write(self):
        raise NotImplementedError

    def read(self):
        return self.get_value()

    def get_value(self):
        self.leftval = self.lhs.read()
        self.rightval = self.rhs.read()
        return self.calc()

    def check_value(self):
        try:
            self.get_value()
            return self.set_complete(True)
        except:
            self.logger.warning('Calculation failure in ', self.id)
            return self.set_complete(False)


#####################Transition Attribute Types (use read functions and compare) #########################
class Compare(AttributeBase):

    operator_dict = {'>': operator.gt,
                     '>=': operator.ge,
                     '==': operator.eq,
                     '=': operator.eq,
                     '<': operator.lt,
                     '<=': operator.le,
                     '!=': operator.ne}

    def __init__(self, lhs=AttributeDummy(), op='', rhs=AttributeDummy(), deadband=0.01):
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

        if isinstance(lhs, AttributeBase) and isinstance(rhs, AttributeBase):
            self.lhs = lhs
            self.rhs = rhs
        else:
            raise TypeError

        self.deadband = deadband  # deadband applied to rhs of comparison

        self.id = self.lhs.tag+self.op+self.rhs.tag

        self.logger = dlog.MakeChild(self.id)

        self.attr_path = ''

        AttributeBase.__init__(self, self.lhs.tag)

        self.leftval = self.lhs.last_read
        self.rightval = self.rhs.last_read

    def read(self):
        '''Returns most recent comparison evaluation'''
        return self.comp_eval()

    def write(self, target_value=None):
        '''Writes target value to self.lhs'''
        if not target_value:
            target_value = self.rhs.read()
        self.logger.debug("Writing %s to %r", target_value, self.lhs)
        return self.lhs.write(target_value=target_value)

    def comp_eval(self):
        '''
        Evaluates comparison:  (lhs) - (rhs) (opr) (deadband)
        Ex. /PI-1875/PV.CV - 65 > 0.1
        '''

        if self.op == '=' or self.op == '==':
            self.op = '=='
            cmp_val = 'abs('+str(self.leftval) +'-'+str(self.rightval)+')<'+str(self.deadband)
        else:
            cmp_val = str(self.leftval) +'-'+str(self.rightval)+self.op+str(self.deadband)

        self.logger.debug('Evaluating: %s', cmp_val)

        return eval(cmp_val)

    def set_read_hook(self, readhook):
        self.lhs.set_read_hook(readhook)
        self.rhs.set_read_hook(readhook)

    def set_write_hook(self, writehook):
        self.lhs.set_write_hook(writehook)
        self.rhs.set_write_hook(writehook)

    def check_value(self):
        self.leftval = self.lhs.read()
        self.rightval = self.rhs.read()

        if self.comp_eval():
            return self.set_complete(True)
        else:
            return self.set_complete(False)

    def force(self):
        '''Attempts to force self.lhs to self.rhs +/- deadband depending on operator type'''
        if '>' in self.opr:  # set rhs = lhs - deadband
            return self.rhs.write(self.lhs.read() - self.deadband)
        elif '<' in self.opr:  # set rhs = lhs + deadband
            return self.rhs.write(self.lhs.read() + self.deadband)
        else:  # set rhs = lhs
            return self.rhs.write(self.lhs.read())


