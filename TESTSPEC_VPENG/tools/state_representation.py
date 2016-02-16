__author__ = 'vpeng'

from puml_dict_parser import GetDict
from TESTSPEC_EKOPACHE.tools import StateAlgo


'''with [*], find it's destination(First Step) in source'''
start = GetDict.source_destination()['*'] #Get the first State after [*]

in_state = start  #List
dest_state = GetDict.source_destination()[start]  # List

for x in range(0,len(in_state))
    for y in range(0,len(dest_state)):
        while dest_state[y] != '[*]':
            '''recurring start'''

            '''add_state'''
            StateAlgo.StateAlgorithm.add_state(state_object = in_state[x])

            '''add_action and evaluate(if any)'''
            if in_state[x] in GetDict.state_action():
                action = GetDict.state_action()[in_state[x]] # List
                for n in range(0,len(action)):
                    StateAlgo.State.add_action(action_obj = action[n])
                    StateAlgo.Action.evaluate(action[n])

            '''find dest_state'''
            dest_states = GetDict.source_destination()[in_state[x]] # List

            '''add_transition (if any)'''
            for z in dest_states:
                connection = (in_state[x], dest_states[z])

                if connection in GetDict.states_transition():
                    transition = GetDict.source_transition()[in_state[x]] #List
                    for m in range(0,len(transition)):
                        StateAlgo.StateAlgorithm.add_trasition(transition = transition[m], current_state = in_state[x],
                                                               next_state = dest_states[z])
                        '''evaluate_transition'''
                        StateAlgo.StateAlgorithm.evaluate_transitions()

                    '''change_state'''
                    permissive = StateAlgo.Transition.check_condition()
                    StateAlgo.StateAlgorithm.change_state(done_state = in_state[x], new_state = dest_states[z],
                                                          check_permissive = permissive)

                else:
                    '''change state'''
                    StateAlgo.StateAlgorithm.change_state(done_state = in_state[x], new_state = dest_states[z],
                                                          check_permissive = True)

                '''recurring...'''#TODO:......
                new_state = dest_state


StateAlgo.StateAlgorithm.deactivate_all()