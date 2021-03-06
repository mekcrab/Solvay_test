__author__ = 'erik'
'''
Module contains class definition for state data model.

Model will be used as an output from plantUML lexer/parser combination.

Model will also be used an input for test generation.
'''

from networkx import DiGraph

from Utilities.Logger import LogTools
dlog = LogTools('StateModel.log', 'StateModel')
dlog.rootlog.warning('Module initialized')


class StateDiagram(DiGraph):
    '''
    Representation of plantUML state diagram.
    Relationships mapped as directed graph, attributes held as graph nodes.
    '''

    def __init__(self, *args, **kwargs):

        self.states = list()  # list of all states in the diagram
        self.top_level = list()  # list of all the top-level states
        self.state_names = {}  # map of states by name to graph node
        self.transitions = list() # dictionary of all transitions in the diagram

        self.id = kwargs.pop('id', 'diagram instance')

        self.logger = dlog.MakeChild('StateDiagram', self.id)

        # Initialize parent class
        DiGraph.__init__(self, *args, **kwargs)

    def get_state(self, state_id, supress_error=False):
        if isinstance(state_id, State):
            return state_id
        else:  # string name of state passed as arg
            state_name = state_id

        if state_name in self.state_names:
            return self.state_names[state_name]
        else:
            if not supress_error:
                self.logger.error("No state named %s exists in diagram", state_name)
            raise NameError

    def print_nodes(self):
        '''prints nodes with friendly names'''
        node_names = [x.name for x in self.nodes()]
        print node_names
        return node_names

    def get_transitions(self, source=None, dest=None):
        '''returns transitions in the diagram
            optionally filtered by source, destination states
            :return: list of transitions matching filter criteria
        '''
        trans_list = self.transitions
        if source:  # filter by source
            source = self.get_state(source)
            trans_list = [x for x in trans_list if source in x.source]
        if dest:  # conjunctive filter by destination
            dest = self.get_state(dest)
            trans_list = [x for x in trans_list if dest in x.dest]
        return trans_list

    def print_edges(self):
        '''prints edges with friendly names'''
        edge_names = [(x.name, y.name) for x,y in self.edges()]
        print edge_names
        return edge_names

    def check_state_exists(self, state_id):
        if (isinstance(state_id, str) or isinstance(state_id, unicode)) and state_id in self.state_names:
            return True
        elif self.has_node(state_id):  # state_id reference is a state object
            return True
        else:
            return False

    def add_state(self, state_name, parent_state=None, attrs=None):
        '''
        Adds a new state to the diagram. Will add substate as appropriate if parent_state
        is defined.
        '''

        if parent_state:
            parent_state = self.get_state(parent_state)

        if self.check_state_exists(state_name):
            new_state = self.get_state(state_name)
        else:
            new_state = State(state_name, parent_state, attributes=attrs)
            self.state_names[state_name] = new_state
            # Add substate to parent if in diagram
            if parent_state:
                self.get_state(parent_state).add_substate(new_state)
            else:
                self.add_node(new_state)
                self.top_level.append(new_state)

        if attrs:
            new_state.add_attribute(attrs)

    def add_state_attr(self, state_id, attribute):
        state = self.get_state(state_id)
        state.add_attribute(attribute)

    def add_transition(self, source, dest, parent_state=None, attributes=None):
        if parent_state:
            parent_state = self.get_state(parent_state)

        # make start and ending states [*] unique for each they are in
        if source in ['[*]', u'[*]']:
            if parent_state:
                source = ' '.join([u'START', parent_state.name])
            else:
                source = u'START'
        if dest in ['[*]', u'[*]']:
            if parent_state:
                dest = ' '.join([u'END', parent_state.name])
            else:
                dest = u'END'

        for state in [source, dest]:
            try:
                self.get_state(state, supress_error=True)
            except NameError:
                self.add_state(state, parent_state=parent_state)

        # get references to state object as required
        source = self.get_state(source); dest = self.get_state(dest)

        # make new transition object and add to diagram.transitions
        new_transition = Transition(source, dest)
        self.transitions.append(new_transition)

        # add attributes if applicable
        if attributes:
            new_transition.add_attribute(attributes)

        # add transition to graph representation
        if parent_state:
            self.get_state(parent_state).substates.add_transition(source, dest, parent_state=None, attributes=attributes)
        else:
            self.add_edge(source, dest, attr_dict={'trans':new_transition})
        # link require source/destination properties of the states
        source.add_destination(dest)
        dest.add_source(source)

    def get_start_states(self, global_scope=False):
        start_states = list()
        for state in self.nodes():
            if state.is_start_state(global_scope):
                start_states.append(state)
        return start_states

    def get_end_states(self, global_scope=False):
        end_states = list()
        for state in self.nodes():
            if state.is_end_state(global_scope):
                end_states.append(state)
        return end_states

    def flatten_graph(self):
        '''
        Flattens recursive structure of State.substates to a single graph by eliminating all superstates
        :return: directed graph of flattened structure
        '''
        flat_graph = self.subgraph(self.nodes())  # retains only nodes and edges in top-level graph - not a copy!!
        for state in flat_graph.nodes():
            # check for subgraph
            if state.num_substates > 0:
                # recursively flatten subgraphs
                subgraph = state.substates.flatten_graph()
                # add resulting subgraph to newly flattened graph
                flat_graph.add_edges_from(subgraph.edges())
                # connect starting edges to superstate.source, ending edges to superstate.destination
                for sub_state in subgraph.nodes():
                    if sub_state.is_start_state():
                        [flat_graph.add_edge(src, sub_state) for src in state.source]
                    if sub_state.is_end_state():
                        [flat_graph.add_edge(sub_state, dest) for dest in state.destination]
                # remove superstate
                flat_graph.remove_node(state)
        return flat_graph

    def get_labeled_graph(self):
        '''returns a graph with nodes identified by state names'''
        labeled_graph = self.subgraph([])  # new subgraph with no nodes
        for state in self.nodes():
            labeled_graph.add_node(state.name)
        for source, destination in self.edges():
            labeled_graph.add_edge(source.name, destination.name)
        return labeled_graph

    def collect_attributes(self):
        '''
        Provides a dictionary of state_id: attribute list
        :return: dictionary
        '''
        attr_dict = dict()
        for state in self.state_names.values():
            attr_dict[state.name] = state.attrs
        return attr_dict


class State(object):

    def __init__(self, name, parent_state=None, **kwargs):
        '''
        Constructor
        :param name: unique name of this state within the diagram <string>
        :return: new state instance
        '''

        self.name = name
        self.attrs = list()
        self.attributes = self.attrs  # overload
        self.substates = StateDiagram()
        self.num_substates = 0
        self.source = list()
        self.destination = list()

        if isinstance(parent_state, State) or parent_state is None:
            self.parent = parent_state
        else:
            dlog.rootlog.error("State parents must also be states - cannot bind parent to %", self.name)
            raise TypeError

    def add_attribute(self, attribute):
        self.attrs.append(attribute)

    def add_substate(self, substate):
        if not isinstance(substate, State):
            raise TypeError
        else:
            self.substates.add_node(substate)
            self.substates.top_level.append(substate)
            self.num_substates += 1

    def get_substate_names(self):
        return [x.name for x in self.substates]

    def is_start_state(self, global_scope=False):
        '''
        Returns True if this state is a starting state in graph level scope.
        Set argument global_scope = True to determine starting condition in the full diagram scope
        :param global_scope: local scope if False (default)
        :return: True if starting state
        '''
        local_start = len(self.source) == 0
        if global_scope and self.parent:
            return local_start and self.parent.is_start_state(global_scope=True)
        else:
            return local_start

    def is_end_state(self, global_scope=False):
        '''
        Returns True if this state is an ending state in the local graph level scope.
        Set argument global_scope = True to determine starting condition in the full diagram scope
        :param global_scope: local scope if False (default)
        :return: True if ending state
        '''
        local_end = len(self.destination) == 0
        if global_scope and self.parent:
            return local_end and self.parent.is_end_state(global_scope=True)
        else:
            return local_end

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

    def print_attributes(self):
        '''Prints out attributes for this state'''
        from pprint import pprint as pp
        pp([(attr, attr.__dict__) for attr in self.attrs])


class Transition(object):
    def __init__(self, source, dest, attrs=None):
        '''
        Constructor
        :return: new Transition with source and destination
        '''
        self.attrs = list()  #List of transition attributes
        self.attributes = self.attrs  # overload
        self.source = list() # list of states
        self.dest = list() # list of states with transitions originating in this state

        # extend lists of sources, destinations and attributes
        self.add_source(source)
        self.add_destination(dest)
        if attrs:
            [self.add_attribute(attr) for attr in attrs]

    def add_attribute(self, attribute):
        try:
            self.attrs.extend(attribute)
        except:  # attribute is not iterable, expecting a list
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

