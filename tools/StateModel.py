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
    def __init__(self):
        '''
        Constructor
        :return: new Transition with source and destination
        '''

        self.attrs = list() #List of transition attributes
        self.TranSource = list() # list of states
        self.TranDest = list() # list of states with transitions originating in this state

    def add_attribute(self, attribute):
        self.attrs.append(attribute)

    def add_source(self, TranSource):
        if not isinstance(TranSource, State):
            raise TypeError
        else:
            self.TranSource.append(TranSource)

    def add_destination(self,TranDest):
        if not isinstance(TranDest, State):
            raise TypeError
        else:
            self.TranDest.append(TranDest)


class Attribute_Base(object):
    def __init__(self):
        self.attrs = list()
        self.keys = list()
        self.complete = False

    def add_attribute(self,attribute):
        if not isinstance(attribute, Attribute_Base):
            raise TypeError
        else:
            self.attrs.append(attribute)

    def evaluate(self):
        #TODO: How do we evaluate if an attribute complete?
        return self.complete


class State_Attr(Attribute_Base):
    def __init__(self):
        Attribute_Base.__init__(self)


class Trans_Attr(Attribute_Base):
    def __init__(self):
        Attribute_Base.__init__(self)




