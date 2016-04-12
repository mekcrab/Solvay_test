__author__ = 'vpeng'

import threading
import time

from serverside.OPCclient import OPC_Connect
from tools.test_generation.TestSolver import TestCase

# Module level log setup
from Utilities.Logger import LogTools
dlog = LogTools('TestAdmin.log', 'TestAdmin')
dlog.rootlog.warning('TestAdmin initialized')


def remove_duplicates(values):
    '''
    Transforms iterable of <values> into a set, effectively removing duplicates BY REFERENCE ID(!!)
    :param values: iterable of objects
    :return: list of above objects without duplicate references
    '''
    cleanup = set(values)
    return list(cleanup)


def make_test_log(filename, rootname):
    '''
    Log factory. Logs will be places in config.log_path by default.
    :return: instance of LogTools - essentially a convenience binding to an existing logging handler.
    '''
    return LogTools(filename, rootname)


class TestAdmin(object):
    '''Class for administration of an individual test case'''
    base_logtool = dlog

    def __init__(self, test_case, connection, poll_interval=0.5, timeout=600, **kwargs):
        '''Constructor'''
        # bind test case, which definies the test to be administered
        if isinstance(test_case, TestCase):
            self.test_case = test_case
            self.diagram = self.test_case.diagram
        else:
            raise TypeError

        # bind runtime connection hooks for reading/writing online values
        #   intended as an OPC client connection, but can be anything with a read() and write() method
        self.connection = connection

        # set new logger to log test case output in a separate file
        # optional arguments for test_id and logging level control
        test_id = kwargs.pop('test_id', test_case.get_name())
        log_level = kwargs.pop('log_level', 'debug')
        self.log_tool = LogTools(test_id+'.log', test_id, level=log_level)
        self.logger = self.log_tool.MakeChild(test_id+'_TestAdmin')

        # global variables to control test timing
        self.poll_interval = poll_interval  # interval between calls to execute states or transitions
        self.global_timeout = timeout  # global timeout if all states not achieved

    def set_attribute_hooks(self, attr_list):
        '''
        Prepares attributes for execution by setting attribute readhook, writehook and loggers.
        :param attr_list: list of AttributeBase instances to be executed in the administered test
        '''
        for attr in attr_list:
            attr.set_log(self.log_tool)
            attr.set_read_hook(self.connection.read)
            attr.set_write_hook(self.connection.write)

    def recur(self, in_state):
        '''Method executes all attribute found in <in_state>'''
        state = self.diagram.get_state(state_id=in_state)
        num_attributes = len(state.attrs)
        complete_count = 0

        self.logger.debug("Testing state::: %r, %r attribute(s) found", state.name, num_attributes)

        # set method hooks for all attributes in the state under test
        self.set_attribute_hooks(state.attrs)

        # grab marker for attribute execution timeout
        mark_timeout = time.time()

        # As long as (not any state.attrs.complete), keep attempting attr.execute at specified polling interval
        last_state_complete_cnt = None
        while 1:
            poll_time = time.time() + self.poll_interval

            # (1) execute test loop if all attributes are not complete
            # each attribute is executed during every polling period -- in case the value changes!!
            # TODO - find out how long attr.execute() method takes for each attribute type (see timeit)
            for attr in state.attrs:
                type_error_mark = []
                complete_count += (attr.get_complete() == True)

                if not attr.get_complete():
                    try:
                        attr.execute()
                    except TypeError:
                        type_error_mark.append(attr)
                        continue

                if type_error_mark: # falls through if list not empty
                    type_error_mark = remove_duplicates(type_error_mark)
                    for type_error in type_error_mark:
                        self.logger.error('Error in %r.execute()', type_error)

            # (2) look at results
            #   (a) check if all attributes have passed,
            # print "complete_count:", complete_count, "num_attr:", num_attributes
            if last_state_complete_cnt != complete_count:
                self.logger.debug("Checking state %s: %d of %d attributes complete",
                                 state.name, complete_count, num_attributes)
                last_state_complete_cnt = complete_count

            if complete_count == num_attributes:
                self.logger.info("Test on State %s Complete", in_state.name)
                return True
            #  (b)  or the state has timed out...
            elif (time.time() - mark_timeout) > self.global_timeout:
                self.logger.error("Time out at state %s, pass to the next test case.", in_state.name)
                return False  # or other timeout logic here!!
            #  (c) otherwise wait for the next polling interval
            else:
                complete_count = 0
                while time.time() < poll_time:
                    pass

    def transit(self, source, destination):
        '''
        Method sets up and executes all attributes in the transition between <source state> and <destination state>
        '''
        source = self.diagram.get_state(state_id=source)
        destination = self.diagram.get_state(state_id=destination)

        transitions = self.diagram.get_transitions(source=source.name, dest=destination.name)

        # setup tracking counters for transition attributes
        # set transition attribute hooks
        if transitions:
            num_attributes = len(transitions[0].attrs) #fixme - implicit assumption we have only one transition?!?!
            for transition in transitions:
                self.set_attribute_hooks(transition.attrs)
        else:
            num_attributes = 0
            self.logger.warning("No transition found between %s and %s", source.name, destination.name)

        complete_count = 0

        self.logger.debug("Testing transition between source state %r and destination state %r",
                  source.name, destination.name)

        # FIXME: empty transition on the diagram is built as one item in the transition list as well.
        # FIXME: (EFK 09APR2016): Also see fixme tab above
        mark_timeout = time.time()
        while 1:
            poll_time = time.time() + self.poll_interval

            for transition in transitions:
                for tran_attr in transition.attrs:
                    type_error_mark = []
                    complete_count += (tran_attr.get_complete() is True)
                    if not tran_attr.get_complete():
                        try:
                            tran_attr.execute()
                        except TypeError:
                            type_error_mark.append(tran_attr)
                            continue  # to next transition

                    if type_error_mark != []:
                        type_error_mark = remove_duplicates(type_error_mark)
                        for type_error in type_error_mark:
                            self.logger.error('Error in %r.execute()', type_error)

            if complete_count == num_attributes:
                #Activate all State Attributes in Destination State
                for dest_attr in destination.attrs:
                    dest_attr.activate()
                return True
            elif (time.time() - mark_timeout) > self.global_timeout:
                self.logger.error("Time out in transition between %s and %s, force to the next state.", source.name,
                                  destination.name)
                return False  # or other timeout logic here!!
            #  (c) otherwise wait for the next polling interval
            else:
                complete_count = 0
                while time.time() < poll_time:
                    pass


class Test(TestAdmin, threading.Thread):
    '''Class for threaded execution of test cases'''

    def __init__(self, test_case, connection, **kwargs):
        '''Constructor'''
        TestAdmin.__init__(self, test_case, connection, **kwargs)
        threading.Thread.__init__(self, name=test_case.get_name())

    def get_start_state(self):
        '''Method to verify there is only a single starting state for the given test.'''
        start_states = self.diagram.get_start_states()  # list of starting states in test_diagram
        # fixme: this is really a check for program bugs where
        # fixme: --> test_case.diagram.get_start_states() returns more than one state!!
        if len(start_states) != 1:
            raise AttributeError
        else:
            return start_states[0]

    def get_end_state(self):
        '''Method to verify there is only a single ending state for the given test.'''
        end_states = self.diagram.get_end_states()  # list of starting states in test_diagram
        # fixme - same comment as in check_start_state
        if len(end_states) != 1:
            raise AttributeError
        else:
            return end_states[0]

    def run(self):
        '''
        Executes the test as defined by self.test_case. Runs in a separate thread of control
        by calling self.start()
        '''

        in_state = self.get_start_state()

        self.logger.info("+++++++++++++++++++++++++++++++ Test Start ++++++++++++++++++++++++++++=")

        # test is executed by calling attribute.execute() for all state and transition
        #   attributes until all attribute._complete flags are true
        while in_state and self.recur(in_state):
            # FIXME: remove duplicated sources/destinations in TestSolver/ModelBuilder
            # FIXME: --> see get_start_state and get_end_state methods above
            next_states = remove_duplicates(in_state.destination)  # A list of possible destinations
            if next_states:  # not empty
                self.logger.info("Transiting...")
                transition_pass = False
                while not transition_pass:
                    for next_state in next_states:
                        self.logger.info("Next_state: %s", next_state.name)
                        transition_pass = self.transit(source=in_state, destination=next_state)
                        in_state = next_state
            elif in_state is self.get_end_state():
                self.logger.info("==============================Test Complete=========================")
            else:
                self.logger.warning("No transition to process for %s!!", in_state.name)


if __name__ == "__main__":
    import config
    import os
    from pprint import pprint as pp
    from ModelBuilder import build_state_diagram
    from Attributes import AttributeBuilder
    from tools.test_generation.TestSolver import TestCaseGenerator

    # very light testing here:
    connection = OPC_Connect()
    time.sleep(1)

    input_diagram = os.path.join(config.specs_path, 'vpeng', 'AttrTest_0.0.puml')

    # create attribute builder instance for solving attributes
    # abuilder = AttributeBuilder.create_attribute_builder(server_ip='127.0.0.1', server_port=5489)
    abuilder = AttributeBuilder.create_attribute_builder(server_ip='10.0.1.200', server_port=5489)

    # ==Build diagram, preprocessor optional==:
    diagram = build_state_diagram(input_diagram, attribute_builder=abuilder, preprocess=True)
    print "Parsed", len(diagram.state_names.values()), "states"
    print "Parsed", len(diagram.get_transitions()), "transitions"

    print "Attributes generated:"
    pp(diagram.get_state_attributes())

    # generate test cases and execute tests
    tests = TestCaseGenerator(diagram)
    opc_client = OPC_Connect()

    for test_case in tests.test_cases.values():
        new_test = Test(test_case=test_case, connection=opc_client)
        new_test.start()
