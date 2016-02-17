__author__ = 'vpeng'

from puml_dict_parser import GetDict, GetList
from TESTSPEC_EKOPACHE.tools import StateAlgo


def recur(in_state):
    StateAlgo.StateAlgorithm().add_state(state_object = in_state)
    Dest = GetDict().source_destination()[in_state] #List
    Action = []

    if in_state in GetList().AState:
        Action = GetDict().state_action()[in_state] #List

    StateAlgo.State(state_id = in_state, actions = Action).activate()

    connection = []
    for item in range(0,len(Dest)):
        connection.append((in_state, Dest[item]))
        if connection[item] in GetDict().states_transition():
            Transition = GetDict().states_transition()[connection[item]] #List
            for n in range(0, len(Transition)):
                StateAlgo.StateAlgorithm().add_trasition(transition = Transition[n],
                                                        current_state = in_state, next_state = Dest[item])



StateAlgo.StateAlgorithm().deactivate_all()

recur('*') #Start

if StateAlgo.StateAlgorithm().evaluate_transitions():
    StateAlgo.StateAlgorithm().change_state(done_state = '*', new_state = Dest, permissive = True)



'''with [*], find it's destination(First Step) in source'''


start = '*'

input = start
dest = GetDict.source_destination()[input] #Get the State (List) after [*]
start_link = (input,dest)

StateAlgo.State(state_id = input).activate()

if start_link in GetDict.states_transition():
    start_transitions = GetDict.states_transition()[start_link]
    StateAlgo.StateAlgorithm.evaluate_transitions()
    StateAlgo.StateAlgorithm.change_state(done_state = input, new_state = dest, check_permissive = True)
else:
    StateAlgo.StateAlgorithm.change_state(done_state = input, new_state = dest, check_permissive = True)

all_dest = GetList().DestState() #List

for item in range(0,len(all_dest)):
    if StateAlgo.State(state_id = all_dest[item]).is_active():

        #TODO: startloop



StateAlgo.StateAlgorithm.deactivate_all()