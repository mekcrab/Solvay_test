__author__ = 'vpeng'

import test_solver_processor

def S_EMC_PRESS_CND():
    test_gen = test_solver_processor.S_EMC_PRESS_CND()
    return test_admin_processor(test_gen)

def S_EMC_CHARGE():
    test_gen = test_solver_processor.S_EMC_CHARGE()
    return test_admin_processor(test_gen)

def S_EMC_CHG_BLWDN():
    test_gen = test_solver_processor.S_EMC_CHG_BLWDN()
    return test_admin_processor(test_gen)


def test_admin_processor(test_gen):
    import time
    from tools.TestAdmin import Test
    from serverside.OPCclient import OPC_Connect, OPCdummy

    connection = OPC_Connect()
    time.sleep(1)

    for test_case in test_gen.test_cases:
        d = test_gen.test_cases[test_case].diagram
        print "Test Case Name:", str(test_case)
        Test(diagram = d, connection = connection).start()