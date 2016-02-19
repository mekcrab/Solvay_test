__author__ = 'vpeng'

from puml_dict_parser import GetDict, GetList
from tools import StateAlgo


def recur(in_state):
    '''after calling the recur function, these things should be done:
    1. Actions (if any) in the in_state are complete
    2. Transitions are checked
    3. For those good transitions, the destination states are activated (except ['*'] as destination)
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

            '''If in_state is a SuperState,
            we run the childStates inside this superstate,
            start with the start point of the childstate'''

            #TODO: SuperState List in GetList module has to be developed.
            if in_state in GetList().SuperState():
                #TODO: SuperState:ChildStart Dictionary has to be developed in GetDict
                recur(GetDict().superstate_childstart()[in_state])


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

                    '''If in_state is a superstate and transition of in_state complete,
                    deactivate all childstates inside the in_state
                    '''
                    #TODO: SuperState:ChildState Dictionary has to be developed in GetDict.
                    if in_state[item] in GetList().SuperState():
                        for item in GetDict().superstate_child():
                            StateAlgo.State(state_id = GetDict().SuperState()[item]).deactivate()


'''Deactivate all at first'''
StateAlgo.StateAlgorithm().deactivate_all()

'''Activate '[*]' State'''
StateAlgo.State(state_id = '[*]').activate()
print '_____________Start Testing...____________'

'''Recursion should start with checking all active states.
It hits END if a destination state is ['*']
'''
AllSource = GetList().SourceState() #Get All Source State in a List

'''Need to check the status (active/not active) of all instances in a state list'''
def check_active(state_list):
    status = []
    for item in range(0,len(state_list)):
        status.append(StateAlgo.State(state_id = state_list[item]).is_active())
        return status # Returns a list of True or False

'''while any state in AllSource is active, keep running the recursion'''
while True in check_active(AllSource):
    for item in range(0,len(AllSource)):
        if StateAlgo.State(state_id = AllSource[item]).is_active():
            recur(AllSource[item])
        check_active(AllSource)


print '___________Test Complete___________'
StateAlgo.StateAlgorithm().deactivate_all()