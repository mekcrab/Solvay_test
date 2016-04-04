__author__ = 'erik'
'''
Module contains class definition for state data model.

Model will be used as an output from plantUML lexer/parser combination.

Model will also be used an input for test generation.
'''

from networkx import DiGraph, topological_sort_recursive

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

    def __deepcopy__(self, memo):
        '''
        Creates a complete copy of the state diagram instance and all underlying states/transitions.
        Attributes are copied by reference. Transition branching flag is preserved from parent transition.
        :param memo:
        :return:
        '''
        diagram_copy = StateDiagram(id=self.id)
        for state in self.nodes():
            diagram_copy.add_state(state.name, parent_state=state.parent, attrs=state.attrs)

        for source, dest, trans_dict in self.edges(data=True):  # dictionary of source, destination, {'trans':<transition instace>}
            source_name = source.name; dest_name = dest.name;
            print trans_dict
            if 'trans' in trans_dict:
                transition = trans_dict['trans']
                attribute_list = transition.attrs  # retrieve transition instance from edge dictionary
                is_branch = transition.is_branch
            else:
                attribute_list = []
                is_branch = None

            # add transition, if it exists, in the copied state
            if source_name in diagram_copy.state_names and dest_name in diagram_copy.state_names:
                t = diagram_copy.add_transition(source_name, dest_name, attributes=attribute_list)
                t.set_branch(is_branch)
            else:
                pass

        return diagram_copy

    def copy(self):
        '''"
        Public" method reference to self.__deepcopy__ - intended to make copy of diagram states/transitions but
        retain attribute instance references
        '''
        return self.__deepcopy__({})

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

    def get_transition(self, source, dest):
        '''returns a single transition bound to the edge between source and destination'''
        edge_dict = self.get_edge_data(source,dest)
        try:
            return edge_dict['trans']
        except NameError:
            return None

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

        return new_state

    def add_state_attr(self, state_id, attribute):
        state = self.get_state(state_id)
        state.add_attribute(attribute)
        return attribute

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

        return new_transition

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
        :return: Copy of the directed graph with a flattened structure
        '''
        flat_graph = self.subgraph(self.nodes())  # retains only nodes and edges in top-level graph - not a copy!!
        for state in flat_graph.nodes():
            # check for subgraph
            if state.num_substates > 0:
                # recursively flatten subgraphs
                subgraph = state.substates.flatten_graph()
                # add resulting subgraph to newly flattened graph, transitions will follow with subgraph edges
                for edge in subgraph.edges_iter(data=True):
                    flat_graph.add_edge(edge[0], edge[1], attr_dict=edge[2])
                # connect starting edges to superstate.source, ending edges to superstate.destination
                for sub_state in subgraph.nodes():
                    # make transition edges from subgrab start/end states to parent state
                    if sub_state.is_start_state():
                        [flat_graph.add_edge(src, sub_state,
                                             attr_dict={'trans':self.get_transition(src, state)})
                         for src in state.source]
                    if sub_state.is_end_state():
                        [flat_graph.add_edge(sub_state, dest,
                                             attr_dict={'trans':self.get_transition(state, dest)})
                         for dest in state.destination]
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

    def get_state_topology(self, reverse=False):
        '''
        Returns a list of states in topological order.
        :param reverse: flag to return results in reverse order (last executed state in first in list)
        '''
        return topological_sort_recursive(self, reverse=reverse)

    def set_branch_flags(self):
        '''
        Sets transition branching flag based on diagram topology.
        :return:
        '''
        transitions = [d['trans'] for u,v,d in self.edges(data=True) if ('trans' in d) and d['trans']]
        for trans in transitions:
            for s in trans.source:
                if len(s.destination) > 1:
                    trans.set_branch(True)
                else:
                    trans.set_branch(False)

    def get_state_attributes(self):
        '''
        Provides a list of state
        :return:
        '''
        attr_dict = dict()
        for state in self.state_names.values():
            attr_dict[state.name] = state.attrs

        return attr_dict

    def get_transition_attributes(self):
        '''
        :return: list of transition attributes
        '''
        attr_list = list()
        [attr_list.append(transition.attrs) for transition in self.get_transitions()]
        return attr_list

    def collect_attributes(self):
        '''
        Provides a dictionary of state_id: attribute list
        :return: dictionary
        '''
        return self.get_state_attributes().values() + self.get_transition_attributes()


class State(object):

    def __init__(self, name, parent_state=None, **kwargs):
        '''
        Constructor
        :param name: unique name of this state within the diagram <string>
        :return: new state instance
        '''

        self.name = name
        self.attrs = list()
        self.attributes = self.attrs  # overload reference
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
        if type(attribute) is list:
            self.attrs.extend(attribute)
        else:
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
        elif source not in self.source:
            self.source.append(source)

    def add_destination(self, destination):
        if not isinstance(destination, State):
           raise TypeError
        elif destination not in self.destination:
            self.destination.append(destination)

    def print_attributes(self):
        '''Prints out attributes for this state'''
        from pprint import pprint as pp
        pp([(attr, attr.__dict__) for attr in self.attrs])


class Transition(object):
    def __init__(self, source, dest, is_branch=None, attrs=None):
        '''
        Constructor
        :return: new Transition with source and destination
        '''
        self.attrs = list()  #List of transition attributes
        self.attributes = self.attrs  # overload
        self.source = list()  # list of states (fixme: should really be a set!!)
        self.dest = list() # list of states with transitions originating in this state

        # extend lists of sources, destinations and attributes
        self.add_source(source)
        self.add_destination(dest)
        if attrs:
            [self.add_attribute(attr) for attr in attrs]

        self.is_branch = is_branch

    def set_branch(self, branch_val):
        '''Sets a flag for this transition to be a part of branching states'''
        self.is_branch = branch_val

    def add_attribute(self, attribute):
        '''Adds attribute to this transition'''
        try:
            self.attrs.extend(attribute)
        except:  # attribute is not iterable, expecting a list
            self.attrs.append(attribute)

    def add_source(self, TranSource):
        '''Adds source state to transition'''
        if not isinstance(TranSource, State):
            raise TypeError
        elif TranSource in self.source:
            print "Source", TranSource, "already in source list"
        else:
            self.source.append(TranSource)

    def add_destination(self, TranDest):
        '''Adds destination state to transition'''
        if not isinstance(TranDest, State):
            raise TypeError
        elif TranDest in self.dest:
            print "Destination", TranDest, "alread in destination list"
        else:
            self.dest.append(TranDest)

