__author__ = 'erik'
'''
Module contains class definition for state data model.

Model will be used as an output from plantUML lexer/parser combination.

Model will also be used an input for test generation.
'''
from time import time
from networkx import DiGraph

class StateDiagram(DiGraph):
    '''
    Representation of plantUML state diagram.
    Relationships mapped as directed graph, attributes held as graph nodes.
    '''

    def __init__(self, *args, **kwargs):

        self.states = list()  # list of all states in the diagram
        self.top_states = list()  # list of all the top-level states
        self.state_names = {}  # map of states by name to graph node
        self.transitions = list() # dictionary of all transitions in the diagram

        # Initialize parent class
        DiGraph.__init__(self)

    def get_state(self, state_id):
        if isinstance(state_id, State):
            return state_id
        else:  # string name of state passed as arg
            state_name = state_id

        if state_name in self.state_names:
            return self.state_names[state_name]
        else:
            print "Adding state named", state_name, "to diagram."
            self.add_state(state_name)

    def get_transitions(self, source=None, dest=None):
        '''returns transitions in the diagram
            optionally filtered by source, destination states
            :return: list of transitions matching filter criteria
        '''
        trans_list = self.transitions
        if source: # filter by source
            source = self.get_state(source)
            trans_list = [x for x in trans_list if x.source == source]
        if dest: # conjunctive filter by destination
            dest = self.get_state(dest)
            trans_list = [x for x in trans_list if x.dest == dest]

        return trans_list

    def check_state_exists(self, state_id):
        if isinstance(state_id, str) and state_id in self.state_names:
            return True
        elif self.has_node(state_id):  # state_id reference is a state object
            return True
        else:
            return False

    def add_state(self, state_name, parent_state=None, attrs=None):
        if self.check_state_exists(state_name):
            new_state = self.get_state(state_name)
        else:
            new_state = State(state_name, parent_state, attributes=attrs)
            self.add_node(new_state)
            self.state_names[state_name] = new_state
        if attrs:
            new_state.add_attribute()

    def add_state_attr(self, state_id, attribute):
        state = self.get_state(state_id)
        state.add_attribute(attribute)

    def add_transition(self, source, dest, attributes=None):
        for state in [source, dest]:
            if not self.check_state_exists(state):
                self.add_state(state)
        # make new transition object
        new_transition = Transition(self.get_state(source), self.get_state(dest))
        # fixme: make into Attribute_Base instance
        if attributes:
            new_transition.add_attribute(attributes)
        # add transition to diagram.transitions
        self.transitions.append(new_transition)
        # add transition to graph representation
        self.add_edge(self.get_state(source), self.get_state(dest), attr_dict={'trans':new_transition})

class State(object):

    def __init__(self, name, parent_state=None, **kwargs):
        '''
        Constructor
        :param name: unique name of this state within the diagram <string>
        :return: new state instance
        '''

        self.name = name
        self.attrs = list()
        self.substates = list()
        self.num_substates = 0
        self.active = False
        self.source = list()
        self.destination = list()

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

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def is_active(self):
        return self.active

    def add_source(self, source):
        if not isinstance(source, State):
            raise TypeError
        else:
            self.source.append(source)

    def add_destination(self, destination):
        if not isinstance(destination, State):
            raise TypeError
        else:
            self.destination.append(destination)

class Transition(object):
    def __init__(self, source, dest, attrs=None):
        '''
        Constructor
        :return: new Transition with source and destination
        '''
        self.attrs = list() #List of transition attributes
        self.source = list() # list of states
        self.dest = list() # list of states with transitions originating in this state

        # extend lists of sources, destinations and attributes
        self.add_source(source)
        self.add_destination(dest)
        if attrs:
            [self.add_attribute(attr) for attr in attrs]

    def add_attribute(self, attribute):
        self.attrs.append(attribute)

    def add_source(self, TranSource):
        if not isinstance(TranSource, State):
            raise TypeError
        else:
            self.source.append(TranSource)

    def add_destination(self, TranDest):
        if not isinstance(TranDest, State):
            raise TypeError
        else:
            self.dest.append(TranDest)


class Attribute_Base(object):
    def __init__(self, *args):
        self.attrs = list()
        self.keys = list()
        self.complete = False
        self.data = list()  # list of timeseries data

    def add_attribute(self,attribute):
        if not isinstance(attribute, Attribute_Base):
            raise TypeError
        else:
            self.attrs.append(attribute)

    def evaluate(self):
        #TODO: How do we evaluate if an attribute complete?
        return self.complete

    def save_value(self, value):
        '''Adds a timestamp, value tuple to this attribute's self.data
        for later retrieval and analysis
        :param: value - any serializable object (ex. float, string, "condition object", tuples ...)
        '''
        self.data.append( (time.time, value))

class State_Attr(Attribute_Base):
    def __init__(self, state_name):
        Attribute_Base.__init__(self, state_name)


class Trans_Attr(Attribute_Base):
    def __init__(self, source, dest):
        Attribute_Base.__init__(self, source, dest)




