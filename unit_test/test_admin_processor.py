__author__ = 'vpeng'

import test_solver_processor
import time
from tools.TestAdmin import Test
from tools.serverside.OPCclient import OPC_Connect, OPCdummy

def S_EMC_PRESS_CND():
    test_gen, diagram = test_solver_processor.S_EMC_PRESS_CND()
    return test_admin_processor(test_gen, diagram)

def S_EMC_CHARGE():
    test_gen, diagram = test_solver_processor.S_EMC_CHARGE()
    return test_admin_processor(test_gen, diagram)

def S_EMC_CHG_BLWDN():
    test_gen, diagram = test_solver_processor.S_EMC_CHG_BLWDN()
    return test_admin_processor(test_gen, diagram)


def test_admin_processor(test_gen, diagram):

    connection = OPC_Connect()
    time.sleep(1)

    for test_case in test_gen.test_cases:
        test_case = test_gen.test_cases[test_case].diagram
        print "Test Case Name:", str(test_case)
        Test(test_case= test_case, diagram = diagram, connection = connection).start()