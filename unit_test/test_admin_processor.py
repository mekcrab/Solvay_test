__author__ = 'vpeng'

import time
import test_solver_processor
from tools.TestAdmin import Test
import tools.serverside.OPCclient as OPCclient

class RunEM():

    def __init__(self):
        pass

    def S_EMC_PRESS_CND(self):
        self.command_dict = {
        'HOLD': 0,
        'CLOSE_ALL': 1,
        'START_VACUUM': 2,
        'STOP_VACUUM': 3,
        'PRESSURE_UP': 4,
        'VENT': 5,
        'DEAERATE': 6,
    }

        test_gen, diagram = test_solver_processor.S_EMC_PRESS_CND()
        return self.test_admin_processor(test_gen, diagram)

    def S_EMC_CHARGE(self):
        self.command_dict = {
        'HOLD': 0,
        'CLOSE_ALL': 1,
        'CHARGE': 2,
        'RESET_TOTALS': 3,
    }

        test_gen, diagram = test_solver_processor.S_EMC_CHARGE()
        return self.test_admin_processor(test_gen, diagram)

    def S_EMC_CHG_BLWDN(self):
        self.command_dict = {
        'HOLD': 0,
        'CLOSE_ALL': 1,
        'CHARGE': 2,
        'RESET_TOTALS': 3,
    }

        test_gen, diagram = test_solver_processor.S_EMC_CHG_BLWDN()
        return self.test_admin_processor(test_gen, diagram)

    def test_admin_processor(self, test_gen, diagram):
        '''
        Processes multiple test cases for multiple diagrams.
        Each test case is administered by the TestAdmin class
        '''

        from tools import TestAdmin

        connection = OPCclient.OPC_Connect(srv_name='OPC.DeltaV.1')
        time.sleep(1)

        dlog = TestAdmin.dlog
        logger = dlog.MakeChild('TestAdmin')
        logger.debug("Start Testing Diagram::: %r", diagram.id)

        test_list = list()
        for solved_path in test_gen.test_cases:
            test_case = test_gen.test_cases[solved_path].diagram
            logger.debug("Testing Solved Test Case: %r", solved_path)

            # Set EM Command path and target
            command_path = '/'.join([str(diagram.id).strip("'"), 'A_COMMAND.CV'])
            command_name = solved_path.split(' ')[1].split('-')[0]
            command = self.command_dict[command_name]

            # Start EM Command
            connection.write(command_path, command)


            new_test = Test(test_case=test_case, diagram=diagram, connection=connection)
            test_list.append(new_test)
            new_test.start()

        return test_list

if __name__ == "__main__":
    RunEM().S_EMC_PRESS_CND()