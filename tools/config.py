'''
Module contains configuration definitions for plantUML tools
'''

__author__ = "erik"

import os, sys
import pprint

# current path of tools folder
tools_path = os.path.dirname(__file__)

# specifications folder
specs_path = os.path.join(tools_path, '..', 'specs')

# test output folder
tests_path = os.path.join(tools_path, '..', 'tests_out')

# logging folder
log_path = os.path.join(tools_path, 'Logs')
log_level = 'debug'

# path to java JRE
java_path = 'java'

# path to plantUML pre-compiled jar file
# plantUML_jar = 'C:\\Users\\vpeng\\.PyCharm40\\config\\plugins\\plantuml4idea\\lib\\plantuml.jar'
plantUML_jar = os.path.join('/','home', 'erik', '.PyCharm40',
                            'config', 'plugins', 'plantuml4idea',
                            'lib', 'plantuml.jar')

class sys_utils:

    '''Aggregated system utilities for convenience'''

    default_stdout = sys.stdout
    default_displayhook = sys.__displayhook__

    @staticmethod
    def pp_hook(value):
        if value != None:
            pprint.pprint(value)

    @staticmethod
    def set_pp_on():
        '''Sets pretty printing as default terminal displayhook'''
        setattr(sys, 'displayhook', sys_utils.pp_hook)

    @staticmethod
    def set_pp_off():
        '''Reverts to default terminal displayhook'''
        setattr(sys, 'displayhook', sys_utils.default_displayhook)


