'''
Contains definitions for attributes that are not tied directly to the System-Under-Test,
such as string and numeric constants.
'''
import time
from AttributeBase import AttributeBase


class Constant(AttributeBase):
    '''Attribute wrapper for constant values like numbers, strings, etc'''

    def __init__(self, value, **kwargs):

        if type(value) in [int, float, str, unicode]:
            self.val = value
        else:
            raise TypeError
        AttributeBase.__init__(self, 'Constant', attr_path='', **kwargs)

    def read(self):
        return (self.val, 'Good', time.ctime())

    def write(self, value):
        self.val = value
        return 'Success'

    def execute(self):
        if not self.exe_start:
            self.start_timer()
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