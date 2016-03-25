'''

Module contains classes for solving StateModel paths
and test definitions in the if/where/then format for
solving test cases specified as a binary tree.
'''

from graph_utils import GraphSolver
import StateModel
import time, os

import config
from Utilities.Logger import LogTools
dlog = LogTools('TestSolver.log', 'TestSolver')
dlog.rootlog.warning('Module initialized')


class TestCase(object):
    '''Single path through a specified state model which can be verified as Pass/Fail'''
    def __init__(self, *args, **kwargs):
        print args
        print kwargs
        self.name = kwargs.pop('name', 'test_case')
        self.diagram = kwargs.pop('diagram', StateModel.StateDiagram())  # list of ordered states that make up the test case path
        self.passed = None
        self.created = time.time()  # generation timestamp
        self.timestamp = time.time()  # testing activity timestamp

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
        self.logger = dlog.MakeChild('TestCaseGenerator', str(self))
        if isinstance(statediagram, StateModel.StateDiagram):
            self.diagram = statediagram
        else:
            self.logger.error("Must pass instance of StateModel for diagram generation")
            raise TypeError

        self.solver = kwargs.pop('test_solver', GraphSolver.GraphSolver(self.diagram))
        self.test_cases = kwargs.pop('test_cases', dict())

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
        test_number = 1
        # iterate over all possible start/end combinations
        for start_state in flat_graph.get_start_states(global_scope=True):
            for end_state in flat_graph.get_end_states(global_scope=True):
                if self.solver.check_path(start_state, end_state):
                    # add a new test case for each subgraph in new_paths list
                    for path_diagram in self.solver.generate_path_graphs(start_state, end_state):
                        print path_diagram.nodes()
                        case_name = start_state.name+'-'+end_state.name+'_'+str(test_number)
                        self.logger.debug('Adding test case %s', case_name)
                        self.test_cases[case_name] = TestCase(name=case_name, diagram=path_diagram)
                        test_number += 1
        return self.test_cases

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
       for case in self.test_cases.values():
            print [state.name for state in case.path]
       print "Total test cases: " + str(len(self.test_cases.values()))

    def draw_solved_graph(self, output_file='solver_graph.svg'):
        '''Draws the output of flattened graph via pygraphviz'''
        flat_graph = self.diagram.flatten_graph()
        labeled_graph = flat_graph.get_labeled_graph()
        self.solver.set_graph(labeled_graph)
        self.solver.draw_graph(output=output_file)

    def draw_test_paths(self, save_path=config.tests_path):
        '''Draws all test case paths to svg files by test case name'''
        for case in self.test_cases.values():
            self.solver.set_graph(case.diagram.get_labeled_graph())
            self.solver.draw_graph(output=os.path.join(save_path,case.name))


if __name__ == "__main__":
    import os
    import config
    import ModelBuilder
    from Attributes import AttributeBuilder

    config.sys_utils.set_pp_on()

    # specify file path to model
    file_path = os.path.join(config.specs_path, 'EM', 'S_EMC_PRESS_CND.puml')

    # create attribute builder instance for solving attributes
    abuilder = AttributeBuilder.create_attribute_builder(server_ip='127.0.0.1', server_port=5489)
    # build StateDiagram instance
    diagram = ModelBuilder.build_state_diagram(file_path, attribute_builder=abuilder, preprocess=True)

    # generate test cases from model
    test_gen = TestCaseGenerator(diagram)
    test_gen.generate_test_cases()

    # verify paths manually (for now)
    print "Drawing possible diagram paths...",
    test_gen.draw_test_paths()
    print "complete."

    print "State diagram complexity: " + str(test_gen.calculate_complexity())
    print "Total test cases: ", len(test_gen.test_cases.keys())

    # generate drawing of flattened graph - will work on getting better syntax
    test_gen.draw_solved_graph()
    print "===============Testing Complete=================="
