__author__ = 'vpeng'

from puml_dict_parser import GetDict, GetList
from TESTSPEC_EKOPACHE.tools import StateAlgo


def recur(in_state):
    '''after calling the recur function, these things should be down:
    1. Actions (if any) in the in_state is complete
    2. Transitions are checked
    3. For those good transitions, the destination state is activated (except ['*'] as destination)
    4. If any transition is gotten through, which means destination state is activated, in_state should be deactivated)
    Therefore, we can keep running the recursion with: in_state = all active states.
    '''

    StateAlgo.StateAlgorithm().add_state(state_object = in_state) # Add in_state
    Action = []

    if in_state in GetList().AState:
        Action = GetDict().state_action()[in_state] #Get List of Actions (if any)

    evaluate_action = StateAlgo.STBase(args = Action).evaluate_actions() # Add Action in state and check if action complete
    dest_state = GetDict().source_destination()[in_state] # Get List of Destination from in_state

    if evaluate_action == True:
        connection = []
        for item in range(0,len(dest_state)):
            connection.append((in_state, dest_state[item]))

            if connection[item] in GetDict().states_transition():
                Transition = GetDict().states_transition()[connection[item]] # Get List of Transitions (if any)
                for n in range(0, len(Transition)): # Add Transitions
                    StateAlgo.StateAlgorithm().add_trasition(transition = Transition[n],
                                                            current_state = in_state, next_state = dest_state[item])

                if StateAlgo.StateAlgorithm().evaluate_transitions():
                    '''Deactivate in_state; activate dest_state (except ['*'])'''
                    if dest_state[item] != '[*]':
                        StateAlgo.StateAlgorithm().change_state(done_state = in_state, new_state = dest_state[item],
                                                                check_permissive = True)
                    else:
                        StateAlgo.State(state_id = in_state).deactivate()


'''Deactivate all at first'''
StateAlgo.StateAlgorithm().deactivate_all()

'''Activate '[*]' State'''
StateAlgo.State(state_id = '[*]').activate()

'''Recursion should start with checking all active states.
It hits END if a destination state is ['*']
'''
AllSource = GetList().SourceState() #Get All Source State in a List

for item in range(0,len(AllSource)):
    if StateAlgo.State(state_id = AllSource[item]).is_active():
        recur(AllSource[item])


StateAlgo.StateAlgorithm().deactivate_all()