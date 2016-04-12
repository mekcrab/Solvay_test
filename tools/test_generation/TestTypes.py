'''
Module contains class definitions for a hierarchy of testing types.

Not all classes are for the direct verification of system specs. Included here are helper
classes to facilitate running of "official" testing, such as TestSetup and TestMonitor.

A description of the classes and intended use cases is as follows:

TestCase:

'''

import time
from tools.Attributes import AttributeTypes
from tools.StateModel import StateDiagram

class TestCase(object):
    '''Single path through a specified state model which can be verified as Pass/Fail'''
    def __init__(self, case_number, *args, **kwargs):

        self.case_no = case_number  # unique integer to server as baseline identifier for this test case

        self.name = kwargs.pop('name', '')  # string identifier of this test case

        # assign specification diagram, can start with blank state diagram if nothing specified
        # StateModel.StateDiagram of the test case path (should be unbranched DAG)
        diagram = kwargs.pop('diagram', StateDiagram())
        if isinstance(diagram, StateDiagram):
            self.diagram = diagram
        else:
            raise TypeError

        self.passed = None
        self.created = time.time()  # generation timestamp
        self.timestamp = time.time()  # testing activity timestamp

    def __repr__(self):
        return "TestCase no."+str(self.case_no)+" "+self.name

    def get_name(self):
        return self.name

    def is_pending(self):
        if self.passed is not None:
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

class PassiveTest(TestCase):
    '''
    Class of test which reads state and transition attributes to verify all attributes achieve
    their target values during the testing.

    The only attributes which are written are those needs to direct the sequence down the specified
    test path
    '''
    pass


class ActiveTest(TestCase):
    '''
    Class of test which actively sets attribute values different from the targets. This is to
    unsure the specified sequence is actively changing attribute values when specified.
    '''
    pass


class Setup(TestCase):
    '''
    Class of test to set the system to a known state prior to running ActiveTest or PassiveTests.
    Generally a test case will require two setups: (1) to reset the unit equipment to known values

    Can possibly be used as a test fixture in future migration to PyTest testing administration.
    '''
    pass


class RandomSetup(Setup):
    '''
    Class which manipulates equipment to a random state as a preparation step for destructive testing.
    '''
    pass


class Monitor(TestCase):
    '''
    Class of test intended to monitor on-line attribute values concurrently with PassiveTest or
    ActiveTest execution. Monitor outputs can be used for supplemental data for in analysis and
    debugging of test results.
    '''
    pass
