__author__ = 'vpeng'

from StateModel import StateDiagram, State, Transition
from serverside.OPCclient import OPC_Connect


def split_attr(attribute):
    attribute = attribute.strip("()")
    splitted = attribute.split(",")
    splitted[0] = splitted[0].strip("'")
    return splitted


class Action():
    def __init__(self, state_attr, connection):
        self.state_attr = state_attr
        tokens = split_attr(state_attr)
        self.connection = connection
        self.PV = tokens[0]
        self.SP = tokens[2] # must be a number now
        self.complete = False
        print "Setting", self.PV, "to", self.SP

    def execute(self):
        w = self.connection.write(PV = self.PV, SP = self.SP)

    def iscomplete(self):
        #TODO: Debug...
        readtup = self.connection.read(self.PV)
        print "=======", readtup
        readvalue = list(readtup)[0]
        if readvalue == float(self.SP):
            self.complete = True
        return self.complete

class TranAttr():
    def __init__(self, tran_attr, connection):
        self.tran_attr = tran_attr
        tokens = split_attr(tran_attr)
        self.connection = connection
        readtup = self.connection.read(PV = tokens[0])
        self.PV = list(readtup)[0]
        #self.PV = self.connection.read(PV = tokens[0])
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
    substates = get_state.substates
    for substate in substates:
        sub = diagram.get_state(state_id = substate)
        subsource = sub.source
        if subsource == []:
            recur(substate, diagram, connection)
        else:
            continue

#Start
#in_state = '[*]'
#State(name = in_state).activate()

def recur(in_state, diagram, connection):
    get_state = diagram.get_state(state_id = in_state)
    print "Testing State:::", get_state.name
    #connection = OPC_Connect()
    destination = get_state.destination
    state_attr = get_state.attrs

    ''' Run substate (if any) or execute action'''
    if int(get_state.num_substates) > 0:
        runsub(in_state, diagram)
    elif int(get_state.num_substates) == 0:
        are_complete = list()
        for action in state_attr:
            a = Action(action, connection)
            a.execute() # execute state attribute

            #TODO: Debug Action().iscomplete()

            '''
            if a.iscomplete():
                are_complete.append(True)
            else:
                are_complete.append(False)
            '''

        if False not in are_complete:
            #print "Test on State %r Pass" %(get_state.name)
            transit(in_state, destination, connection)
        else:
            print "Test on State %r Fail" %(get_state.name)


def transit(in_state, destination, connection):

    for dest_state in destination:

        '''Transition Attribute'''
        tran_attr = diagram.get_transitions(source=in_state, dest=dest_state)

        reached = list()

        for item in tran_attr:

            if TranAttr(item, connection).verify():
                reached.append(True)
            else:
                reached.append(False)

        if False not in reached:
            get_dest = diagram.get_state(state_id = dest_state)
            dest_name = get_dest.name
            #State(name = in_state).deactivate()
            if get_dest.name != 'END' or []:
                #State(name = dest_state).activate()
                recur(dest_state, diagram, connection)
            elif get_dest.name == 'END':
                print "===========Test Complete=========="


if __name__ == "__main__":
    from ModelBuilder import StateModelBuilder
    from PlantUML_Lexer import get_tokens_from_file
    import config, os, time
    connection = OPC_Connect()

    time.sleep(2)

    input_path = os.path.join(config.specs_path, 'vpeng', 'Demo.puml')

    tkns = get_tokens_from_file(input_path)

    builder = StateModelBuilder()
    diagram = builder.parse(tkns)

    print "===========Test Start=========="

    recur(in_state = "[*]", diagram = diagram, connection = connection)

