'''
Module contains abstract definitions for constructing graphs of state-based algorithms.

Node = Non-exclusive state
Directed Edge = Transition between states

Examples:
    DeltaV Sequential Function Charts
    PROVOX unit code
'''

__author__ = 'erik.kopache'

import ScannedAlgo
from networkx.classes.digraph import DiGraph


class Condition(object):
    '''
    Condition class determines if a given transition will be evaluated,
    causing the system to change state and execute any relavant actions.
    '''

    def __init__(self, *args, **kwargs):
        self.expression = kwargs.pop('expression', None)
        self.value = False

    def is_true(self):
        return self.value

    def evaluate(self):
        raise NotImplementedError


class Action(ScannedAlgo.ScannedAlgorithm):
    '''
    Actions are single-scan data manipulations executed either:
    (1) On a change of state
    (2) Continuously while the parent state is active
    '''

    def __init__(self, *args, **kwargs):
        ScannedAlgo.ScannedAlgorithm.__init__(self, args, kwargs)
        self.complete = False

    def evaluate(self):
        raise NotImplementedError


class STBase(object):
    '''Base class for State and Transition classes'''

    def __init__(self, *args, **kwargs):
        self.actions = []
        self.active = False

        # single action by positional argument, list of actions by keyword argument
        if args:
            [self.add_action(self, arg) for arg in args]
        else:
            [self.add_action(item) for item in kwargs.pop('actions', [])]

    def add_action(self, action_obj):
        '''Adds a paralell action to the state/transition'''
        if not isinstance(action_obj, Action):
            raise TypeError
        else:
            self.actions.append(action_obj)

    def evaluate_actions(self):
        '''Wrapper for evaluation call on all pending actions'''
        [action.evaluate() for action in self.actions if not action.complete]


class Transition(STBase):
    '''
    Class representing a transition between states.
    A transition must have:
        ** one and only one Condition
        ** zero to many Actions
    '''
    def __init__(self, condition = Condition(expression="True"), *actions, **kwargs):
        '''Constructor. A trivial transition has a condition.express=<True>
        and executes a null action'''
        self.id = kwargs.pop('id', None)

        if not isinstance(condition, Condition): raise TypeError
        else: self.condition = condition

        STBase.__init__(self, actions, kwargs)

    def is_active(self):
        '''Checks if transition if active, i.e. guarding condition is <True>'''
        return self.active

    def check_condition(self):
        '''Determine if the guarding condition is true'''
        self.active = self.condition.evaluate()
        return self.active


class State(STBase):
    '''
    Class representing a system or execution state.
    A state may have zero or more actions that are considered
    to be continuously evaluated while the state is active.
    '''
    def __init__(self, state_id, *actions, **kwargs):
        self.id = state_id
        STBase.__init__(self, actions, kwargs)

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def is_active(self):
        return self.active


class StateAlgorithm(DiGraph):
    '''directed graph representation of state based algorithm

    States are represented by nodes
        note -  nodes can be recursive, i.e. a given superstate consisting of multiple substates

    Edges are represented by transitions
        Transition actions are guarded by one or more conditions which required a <True>
        evaluation before execution of the transition actions
        Transition actions are equivalent to the actions taken in the next state -
            i.e. once a transitions condition evaluates as True, the system is
            considered to be in the state pointed to by that transition
    '''

    def __init__(self, algo_id, *args, **kwargs):
        self.id = algo_id
        self.active_states = []
        self.state_id_dict = {}        # dictionary of state.id aliases for convenient node/edge lookups
        DiGraph.__init__(self, args, kwargs)

    def add_state(self, state_object):
        '''
        Adds a state to the graph. States can be stand alone or recursive 'superstates'
        '''
        if not (isinstance(state_object, State) or isinstance(state_object, StateAlgorithm)):
            raise TypeError
        self.add_node(self, state_object, attr_dict=state_object.__dict__)

    def add_trasition(self, transition, current_state, next_state):
        if not isinstance(transition, Transition):
            raise TypeError
        self.add_edge(current_state, next_state, attr_dict=Transition.__dict__)

    def get_node_by_id(self, node_id):
        return self.node[self.state_id_dict[node_id]]

    def get_state_by_id(self, state_id):
        return self.get_node_by_id(state_id)

    def get_edge_by_id(self, from_id, to_id):
        return self.edge[self.get_node_by_id(from_id), self.get_node_by_id(to_id)]

    def get_trans_by_id(self, state_from_id, state_to_id):
        return self.get_edge_by_id(state_from_id, state_to_id)

    def activate_state(self, state):
        if state not in self:
            state = self.get_state_by_id(state)
        state.activate()
        self.active_states.append(state.id)

    def deactivate_state(self, state):
        if state not in self:
            state = self.get_state_by_id(state)
        state.deactivate()
        self.active_states.pop(state.id)

    def evaluate_transitions(self):
        '''
        Executes state change based on transition evaluation.
        '''
        #ToDo: verify this will allow moving from a single completed state to multiple active states
        active_states = [self.get_state_by_id(current_state_id) for current_state_id in self.active_states]
        for current_state in active_states:
            [self.change_state(current_state, next_state, check_permissive=False) for
                next_state in self.successors(current_state) if
                self.edge[current_state, next_state].evaluate()
             ]

    def change_state(self, done_state, new_state, check_permissive=True):
        '''
        Tracks a state transition from done_state to new_state. Check_permissive
        flag ensures valid connection between states in question.
        :param done_state           State to be exited
        :param new_state            State to be started
        :param check_permissive     Verify a transition exists allowing the state change
        '''
        if check_permissive and not (new_state in self.successors(done_state)):
            raise ValueError
        else:
            self.deactivate_state(done_state)
            self.activate_state(new_state)

    def is_active(self):
        '''The StateAlgorithm is considered active if any states are active'''
        return len(self.active_states) > 0

    def deactivate_all(self):
        '''Deactivates all currently active states.'''
        [self.deactivate_state(state_id) for state_id in self.active_states]

