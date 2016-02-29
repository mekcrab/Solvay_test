'''

Module contains classes for solving StateModel paths
and test definitions in the if/where/then format for
solving test cases specified as a binary tree.
'''

from graph_utils import GraphSolver
import StateModel
import time

class TestCase(object):
    '''Single path through a specified state model which can be verified as Pass/Fail'''
    def __init__(self, *args, **kwargs):

        self.name = kwargs.pop('name', None)

        self.passed = None
        self.timestamp = time.time()
        self.path = kwargs.pop('state_list', list())  # list of ordered states that make up the test case path

    def get_name(self):
        return self.name

    def is_pending(self):
        if type(self.passed) is not type(None):
            return False
        else:
            return True

    def has_passed(self):
        if not self.is_pending():
            return self.passed
        else:
            return None

    def update_timestamp(self):
        '''
        Updates timestamp of most recent activity - test pass/fail or generation time
        :return:
        '''
        self.timestamp = time.time()

class TestCaseGenerator(object):
    '''
    Generates a series of TestCase instances from a given StateDiagram instance
    '''
    def __init__(self, statediagram, *args, **kwargs):
        if isinstance(statediagram, StateModel.StateDiagram):
            self.diagram = statediagram
        else:
            print "Must pass instance of StateModel for diagram generation"
            raise TypeError

        self.solver = kwargs.pop('test_solver', GraphSolver.GraphSolver(self.diagram))
        self.test_cases = kwargs.pop('test_case_dict', dict())

    def generate_test_cases(self):
        '''
        Method to generate test cases for all linear paths through state diagram.
        :return:
        '''
        path_list = list()  # list of paths through the diagram
        # flatten state model diagram
        flat_graph = self.diagram.flatten_graph()
        # generate linear state model for each path through graph from each possible starting state to each ending state
        self.solver.set_graph(flat_graph)
        for start_state in self.diagram.get_start_states():
            for end_state in self.diagram.get_end_states():
                path_list.extend(self.solver.generate_paths(start_state, end_state))
        # add a new test case for each case in path_list
        for path in path_list:
            self.test_cases[str(path)] = TestCase(state_list = path)

        return path_list

    def calculate_complexity(self):
        '''
        Calculates cyclomatic complexity of the given state diagram
        :return:
        '''
        flat_graph = self.diagram.flatten_graph()
        self.solver.set_graph(flat_graph)
        return self.solver.calculate_complexity()

    def get_failed_cases(self):
       '''
       :return: list of failed test cases
       '''
       return [case.name for case in self.test_cases if not case.has_passed()]

    def get_passed_cases(self):
        '''
        :return: list of passed test cases
        '''
        return [case.name for case in self.test_cases if case.has_passed()]

    def get_pending_cases(self):
       '''
       :return: list of pending test cases
       '''
       return [case.name for case in self.test_cases.values() if case.is_pending()]

    def print_test_cases(self):
       '''
       Prints the generates paths for self.diagram
       :return:
       '''
       print "Total test cases: " + str(len(self.test_cases.values()))
       for case in self.test_cases.values():
            print [state.name for state in case.path]


if __name__ == "__main__":
    import os
    import config
    import ModelBuilder

    config.sys_utils.set_pp_on()

    # specify file path to model
    file_path = os.path.join(config.specs_path, 'vpeng', 'Demo_3.0.puml')
    # build StateDiagram instance
    diagram = ModelBuilder.build_state_diagram(file_path)

    # generate test cases from model
    test_gen = TestCaseGenerator(diagram)
    print "State diagram complexity: " + str(test_gen.calculate_complexity())
    test_gen.generate_test_cases()
    # verify paths manually (for now)
    print "Possible diagram paths: "
    test_gen.print_test_cases()
    test_gen.solver.draw_graph()

    print "===============Testing Complete=================="

