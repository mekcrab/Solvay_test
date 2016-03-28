__author__ = 'vpeng'

import test_solver_processor
import time
from tools.TestAdmin import Test
from tools import TestAdmin
from tools.serverside.OPCclient import OPC_Connect, OPCdummy

dlog = TestAdmin.dlog

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

    logger = dlog.MakeChild('TestAdmin')
    logger.debug("Start Testing Diagram::: %r", diagram.id)

    for solved_path in test_gen.test_cases:
        test_case = test_gen.test_cases[solved_path].diagram
        logger.debug("Testing Solved Test Case: %r", solved_path)
        Test(test_case= test_case, diagram = diagram, connection = connection).start()