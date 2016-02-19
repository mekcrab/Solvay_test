'''
Module contains configuration definitions for plantUML tools
'''

__author__ = "erik"

import os

# current path of tools folder
tools_path = os.getcwd()

# specifications folder
specs_path = os.path.join(tools_path, '..', 'specs')

# test output folder
tests_path = os.path.join(tools_path, '..', 'tests_out')

# path to java JRE
java_path = 'java'

# path to plantUML pre-compiled jar file
plantUML_jar = '/home/erik/.PyCharm40/config/plugins/plantuml4idea/lib/plantuml.jar'

class sys_utils():

    '''Aggregated system utilities for convenience'''

    def set_pp_on(self):
        '''Sets pretty printing as default terminal displayhook'''
        pass

    def set_pp_off(self):
        '''Reverts to default terminal displayhook'''
        pass


