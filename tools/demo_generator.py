__author__ = 'vpeng'

from StateModel import StateDiagram, State, Transition
import OpenOPC

class OPC_Connect:

    def __init__(self):
        self.client = self.connect_local('OPC.DeltaV.1')


    def connect_local(self, svr_name):

        opc_client = OpenOPC.open_client('localhost')
        opc_client.connect(svr_name)
        return opc_client


def split_attr(attribute):
    attribute = attribute.strip("()")
    splitted = attribute.split(",")
    return splitted


class Action:
    def __init__(self, state_attr):
        self.state_attr = state_attr
        tokens = split_attr(state_attr)
        self.PV = OPC_Connect().client.read(tokens[0])
        self.SP = float(tokens[2]) # must be a number now
        self.complete = False

    def iscomplete(self):
        if self.PV == self.SP:
            self.complete = True
        return self.complete


    def execute(self):
        OPC_Connect().client.write((self.PV, self.SP))

class TranAttr:
    def __init__(self, tran_attr):
        self.tran_attr = tran_attr
        tokens = split_attr(tran_attr)
        self.PV = OPC_Connect().client.read(tokens[0])
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


def runsub(parent):
    get_state = StateDiagram().get_state(state_id = parent)
    state_dict = get_state.__dict__
    substates = state_dict['substates']
    for x in range(0,len(substates)):
        sub = StateDiagram().get_state(state_id = substates[x])
        subsource = sub.__dict__['source']
        if subsource == []:
            recur(substates[x], diagram)
        else:
            continue

#Start
#in_state = '[*]'
#State(name = in_state).activate()

def recur(in_state, diagram):
    get_state = diagram.get_state(state_id = in_state)

    state_dict = get_state.__dict__
    destination = state_dict['destination']
    state_attr = state_dict['attrs']

    ''' Run substate (if any) or execute action'''
    if state_dict['substate_num'] > 0:
        runsub(in_state)
    elif state_dict['substate_num'] == 0:
        are_complete = list()
        for action in state_attr:
            Action(state_attr = action).execute() # execute state attribute

            if Action(state_attr = action).iscomplete() == True:
                are_complete.append(True)
            else:
                are_complete.append(False)

            if False not in are_complete:
                print "Test on State %r Pass" %(in_state)
            else:
                print "Test on State %r Fail" %(in_state)


    for dest_state in destination:

        '''Transition Attribute'''
        tran_attr = StateDiagram().get_edge_data(u = in_state, v = dest_state)

        reached = list()
        for item in tran_attr:
            if TranAttr(tran_attr = item).verify() == True:
                reached.append(True)
            else:
                reached.append(False)

        if False not in reached:
            State(name = in_state).deactivate()
            if destination != '[*]':
                State(name = destination).activate()
                recur(destination, diagram)


if __name__ == "__main__":
    from ModelBuilder import StateModelBuilder
    import config, os
    from plantUML_state_lexer import get_tokens_from_file

    input_path = os.path.join(config.specs_path, 'vpeng', 'PH_AL_SMPL_CVAS.puml')

    tkns = get_tokens_from_file(input_path)

    builder = StateModelBuilder()
    diagram = builder.parse(tkns)

    recur(in_state = "[*]", diagram = diagram)


    print "=================== Testing Complete ==================="
