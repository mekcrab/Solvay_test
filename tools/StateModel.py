__author__ = 'erik'
'''
Module contains class definition for state data model.

Model will be used as an output from plantUML lexer/parser combination.

Model will also be used an input for test generation.
'''

class StateDiagram(object):
    '''
    Data representation of plantUML state diagram.
    '''

    def __init__(self):
        self.states = list() #list of all states in the diagram
        self.top_states = list() # list of all the top-level states



class State(object):

    def __init__(self, name):
        '''
        Constructor
        :param name: unique name of this state within the diagram <string>
        :return: new state instance
        '''

        self.name = name

        self.attrs = list()
        self.substates = list()
        self.num_substates = 0
        self.source = list() # list of states
        self.destination = list() # list of states with transitions originating in this state

    def add_attribute(self, attribute):
        self.attrs.append(attribute)

    def add_substate(self, substate):
        if not isinstance(substate, State):
            raise TypeError
        else:
            self.substates.append(substate)
            self.num_substates += 1

    def get_substate_names(self):
        return [x.name for x in self.substates]






class attribute_base(object):
    pass

class state_attr(attribute_base):
    pass

class trans_attr(attribute_base):
    pass


