__author__ = 'vpeng'

import time
import test_solver_processor
import tools.serverside.OPCclient as OPCclient
from tools import TestAdmin


class RunEM():

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

        opc_connection = OPCclient.OPC_Connect(srv_name='OPC.DeltaV.1')

        time.sleep(1)

        logger = TestAdmin.dlog.MakeChild('TestAdmin')
        logger.debug("Starting Tests for Diagram::: %r", diagram.id)

        test_list = list()

        # Process a single test instance per path in test_gen.test_cases
        for solved_path in test_gen.test_cases:
            test_case = test_gen.test_cases[solved_path]

            logger.debug("Preparing to execute test case: %r", solved_path)

            # create new test instance
            new_test = TestAdmin.Test(test_case=test_case,
                                      connection=opc_connection,
                                      log_level='info',
                                      test_id=diagram.id  # test_id also is name of log item
                                      )

            # Set EM Command path and target
            command_path = '/'.join([str(diagram.id).strip("'"), 'A_COMMAND.CV'])
            command_name = solved_path.split(' ')[1].split('-')[0]
            command = self.command_dict[command_name]
            # verification path == command path for dummy OPC client
            if opc_connection.is_dummy:
                verify_path = command_path
            else:
                verify_path = '/'.join([str(diagram.id).strip("'"), 'A_TARGET.CV'])

            # Start EM command, verify command has started
            while opc_connection.read(verify_path)[0] != command:
                opc_connection.write(command_path, command)
                time.sleep(0.5)

            test_list.append(new_test)
            # start Test thread, allow to run to completion
            # new_test.start()
            # new_test.join()

            # to run without a new thread, just call run()
            new_test.run()

        return test_list

if __name__ == "__main__":
    # example test
    RunEM().S_EMC_PRESS_CND()