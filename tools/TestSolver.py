'''

Module contains classes for solving StateModel paths
and test definitions in the if/where/then format for
solving test cases specified as a binary tree.
'''

import time
import config
import StateModel
from graph_utils import GraphSolver
from Attributes import AttributeTypes

from Utilities.Logger import LogTools
dlog = LogTools('TestSolver.log', 'TestSolver')
dlog.rootlog.warning('Module initialized')


class TestCase(object):
    '''Single path through a specified state model which can be verified as Pass/Fail'''
    def __init__(self, *args, **kwargs):

        self.name = kwargs.pop('name', 'test_case')
        self.diagram = kwargs.pop('diagram', StateModel.StateDiagram())  # StateModel.StateDiagram of the test case path

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

    def set_passed(self):
        '''Sets the test case as "passed"'''
        self.update_timestamp()
        self.passed = True

    def set_failed(self):
        '''Sets the test case as "failed"'''
        self.update_timestamp()
        self.passed = False

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

    def add_path_directives(self):
        '''
        Adds forced attributes to TestCase to ensure the test utilizes the intended path
            for each CompareAttribute instance in the path's transitions.

        Attributes to force are determined by inclusion in transition comparisons. The left hand side (lhs) of these
            compares will be forced in the 2 states preceding the transition in question, back-calculated to
            the attribute which writes to the value chain earliest in the TestCase path.

        Forced attributes are added to a states specifically for this test case.

        :return: List of forced attributes added
        '''
        def compare_attribute_list(attribute, other_list):
            equal_paths = list()
            if isinstance(attribute, AttributeTypes.Compare):
                equal_paths += [compare_attribute_list(a, other_list) for a in [attribute.lhs, attribute.rhs]]
            elif type(attribute) is list:
                equal_paths += [compare_attribute_list(a, other_list) for a in attr]
            else:
                equal_paths = [a for a in other_list if a == attribute]
            return equal_paths

        force_attrs = dict()  # dictionary of {<state to force value>: <force attribute>}

        # get topological list of states and transitions
        state_order = self.diagram.get_state_topology(reverse=True)

        # work through attr transition attributes in reverse order
        # back calculate transition attribute, mapping any prior references
        for source in state_order[1:]:  # no transition connected to last state
            s, dest, edge_dict = self.diagram.edges(source, data=True)[0]
            if s is not source:
                raise ValueError
            # check for updates written to forced attributes
            for src_state, attr in force_attrs.items():
                attr_update = compare_attribute_list(attr, source.attrs)  # attr can become a list
                if attr_update:
                    force_attrs.update({source:attr})
                    force_attrs.pop(src_state)

            if 'trans' in edge_dict:
                transition = edge_dict['trans']
                if transition.is_branch:
                    force_attrs.update({source:[attr.copy() for attr in transition.attrs]})
            else:
                continue
            # make a new attribute for the topological "top" of the reference map, setting the execute() method to "force"
            # the value reference (as read from runtime system if required)

        # set default test method to 'force', and add to transition prior to branching
        for src_state, attrs in force_attrs.items():
            [a.set_execute(test_method='force') for a in attrs]
            src_state.add_attribute(attrs)

        # return forced attribute dictionary
        return force_attrs

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
        # flatten state model diagram, set flags for branching transitions
        flat_graph = self.diagram.flatten_graph()
        flat_graph.set_branch_flags()
        # generate linear state model for each path through graph from each possible starting state to each ending state
        self.solver.set_graph(flat_graph)
        test_number = 1
        # iterate over all possible start/end combinations
        for start_state in flat_graph.get_start_states(global_scope=True):
            for end_state in flat_graph.get_end_states(global_scope=True):
                if self.solver.check_path(start_state, end_state):
                    # add a new test case for each subgraph in new_paths list
                    for path_diagram in self.solver.generate_path_graphs(start_state, end_state):
                        case_name = start_state.name+'-'+end_state.name+'_'+str(test_number)
                        self.logger.debug('Adding test case %s', case_name)
                        test_case = TestCase(name=case_name, diagram=path_diagram.copy())
                        test_case.add_path_directives()
                        self.test_cases[case_name] = test_case
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
            self.solver.draw_graph(output=os.path.join(save_path, case.name))


if __name__ == "__main__":
    import os
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

    t = test_gen.test_cases.values()[0]

    print "===============Testing Complete=================="
