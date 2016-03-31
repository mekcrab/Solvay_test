'''
Contains definitions for attributes that are not tied directly to the System-Under-Test,
such as string and numeric constants.
'''
import time
from AttributeBase import AttributeBase


class Constant(AttributeBase):
    '''Attribute wrapper for constant values like numbers, strings, etc'''
    mode_int_dict = \
            {'LO': 4, 'MAN': 8, 'AUTO': 16, 'CAS': 32, 'ROUT': 128, 'RCAS': 64}

    def __init__(self, value, **kwargs):

        if type(value) in [int, float, str, unicode]:
            self.val = value
        else:
            raise TypeError
        AttributeBase.__init__(self, 'Constant', attr_path='', **kwargs)

    def OPC_path(self):
        return self.tag + ' ' + str(self.val)

    def read(self):
        if self.val in Constant.mode_int_dict:
            self.val = Constant.mode_int_dict[self.val]
        return self.val
        # return (self.val, 'Good', time.ctime())

    def write(self, value):
        self.val = value
        return 'Success'

    def check_value(self):
        val = self.read()[0]
        if self.read()[0] == self.target_value:
            self.set_complete(True)
        else:
            self.set_complete(False)
        return val

    def force(self, target_value=None):
        if not target_value:
            target_value = self.target_value
        return self.write(target_value)