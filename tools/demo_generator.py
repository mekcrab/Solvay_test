__author__ = 'vpeng'

from StateModel import StateDiagram, State, Transition
from serverside.OPCclient import OPC_Connect


def split_attr(attribute):
    attribute = attribute.strip("()")
    splitted = attribute.split(",")
    return splitted


class Action:
    def __init__(self, state_attr):
        self.state_attr = state_attr
        tokens = split_attr(state_attr)
        self.PV = tokens[0]
        self.SP = float(tokens[2]) # must be a number now
        self.complete = False

    def iscomplete(self):
        if (self.execute() == 'Success') == True:
            self.complete = True
        return self.complete

    def execute(self):
        return OPC_Connect().write(PV = self.PV, SP = self.SP)


class TranAttr:
    def __init__(self, tran_attr):
        self.tran_attr = tran_attr
        tokens = split_attr(tran_attr)
        self.PV = OPC_Connect().read(PV = tokens[0])
        self.condition = tokens[1]
        self.target = float(tokens[2]) # must be a number now
        self.reached = False

    def verify(self):
        if '=' in self.condition and ('>' or '<' or '!') not in self.condition and self.PV == self.target:
            self.reached = True
        elif '>' in self.condition and '=' not in self.condition and self.PV > self.target:
            self.reached = True
        elif '=' and '>' in self.condition and self.PV >= self.target:
            self.reached = True
        elif '=' and '<' in self.condition and self.PV <= self.target:
            self.reached = True
        elif '<' in self.condition and '=' not in self.condition and self.PV < self.target:
            self.reached = True
        elif '!' in self.condition and self.PV != self.target:
            self.reached = True
        else:
            raise TypeError

        return self.reached


def runsub(parent, diagram):
    get_state = diagram.get_state(state_id = parent)
    state_dict = get_state.__dict__
    substates = state_dict['substates']
    for substate in substates:
        sub = diagram.get_state(state_id = substate)
        subsource = sub.__dict__['source']
        if subsource == []:
            recur(substate, diagram)
        else:
            continue

#Start
#in_state = '[*]'
#State(name = in_state).activate()


def recur(in_state, diagram):
    get_state = diagram.get_state(state_id = in_state)

    destination = get_state.destination
    state_attr = get_state.attrs

    ''' Run substate (if any) or execute action'''
    if int(get_state.num_substates) > 0:
        runsub(in_state, diagram)
    elif int(get_state.num_substates) == 0:
        are_complete = list()
        for action in state_attr:
            Action(state_attr = action).execute() # execute state attribute

            if Action(state_attr = action).iscomplete() == True:
                are_complete.append(True)
            else:
                are_complete.append(False)

        if False not in are_complete:
            print "Test on State %r Pass" %(in_state)
            #transit(in_state, destination)
        else:
            print "Test on State %r Fail" %(in_state)

#def transit(in_state, destination)
    for dest_state in destination:

        '''Transition Attribute'''
        tran_attr = diagram.get_edge_data(u = in_state, v = dest_state)

        reached = list()
        for item in tran_attr:
            if TranAttr(tran_attr = item).verify() == True:
                reached.append(True)
            else:
                reached.append(False)

        if False not in reached:
            State(name = in_state).deactivate()
            if destination != '[*]' or []:
                State(name = destination).activate()
                recur(destination, diagram)
            elif destination == '[*]':
                print "===========Test Complete=========="


if __name__ == "__main__":
    from ModelBuilder import StateModelBuilder
    import config, os
    from PlantUML_Lexer import get_tokens_from_file

    input_path = os.path.join(config.specs_path, 'vpeng', 'PH_AL_SMPL_CVAS.puml')

    tkns = get_tokens_from_file(input_path)

    builder = StateModelBuilder()
    diagram = builder.parse(tkns)

    recur(in_state = "[*]", diagram = diagram)



