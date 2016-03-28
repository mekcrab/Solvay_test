__author__ = 'vpeng'

import os
from tools import config, ModelBuilder, TestSolver
from tools.Attributes import AttributeBuilder

def S_EMC_PRESS_CND():
    return test_solver_processor(test_class='EM', test_spec='S_EMC_PRESS_CND.puml')

def S_EMC_CHARGE():
    return test_solver_processor(test_class='EM', test_spec='S_EMC_CHARGE_V2.puml')

def S_EMC_CHG_BLWDN():
    return test_solver_processor(test_class='EM', test_spec='S_EMC_CHG_BLWDN.puml')

def test_solver_processor(test_class, test_spec):

    config.sys_utils.set_pp_on()

    # specify file path to model
    file_path = os.path.join(config.specs_path, test_class, test_spec)

    # create attribute builder instance for solving attributes
    # abuilder = AttributeBuilder.create_attribute_builder(server_ip='127.0.0.1', server_port=5489)
    abuilder = AttributeBuilder.create_attribute_builder(server_ip='10.0.1.200', server_port=5489)
    # build StateDiagram instance
    diagram = ModelBuilder.build_state_diagram(file_path, attribute_builder=abuilder)

    # generate test cases from model
    test_gen = TestSolver.TestCaseGenerator(diagram)
    test_gen.generate_test_cases()

    # verify paths manually (for now)
    print "Drawing possible diagram paths...",
    # test_gen.draw_test_paths()
    print "complete."

    print "State diagram complexity: " + str(test_gen.calculate_complexity())
    print "Total test cases: ", len(test_gen.test_cases.keys())

    # generate drawing of flattened graph - will work on getting better syntax
    # test_gen.draw_solved_graph()

    return test_gen, diagram

if __name__ == "__main__":
    S_EMC_PRESS_CND()