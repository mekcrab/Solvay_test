__author__ = 'vpeng'

import test_solver_processor
import time
from tools.TestAdmin import Test
from tools.serverside.OPCclient import OPC_Connect, OPCdummy

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

        connection = OPC_Connect()
        time.sleep(1)

        from tools import TestAdmin

        dlog = TestAdmin.dlog
        logger = dlog.MakeChild('TestAdmin')
        logger.debug("Start Testing Diagram::: %r", diagram.id)

        for solved_path in test_gen.test_cases:
            test_case = test_gen.test_cases[solved_path].diagram
            logger.debug("Testing Solved Test Case: %r", solved_path)

            # Set EM Command path and target
            command_path = '/'.join([str(diagram.id).strip("'"),'A_COMMAND.CV'])
            command_name = solved_path.split(' ')[1].split('-')[0]
            command = self.command_dict[command_name]

            # Start EM Command
            connection.write(command_path, command)

            Test(test_case=test_case, diagram=diagram, connection=connection).start()


if __name__ == "__main__":
    RunEM().S_EMC_PRESS_CND()