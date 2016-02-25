__author__ = 'vpeng'

from StateModel import StateDiagram, State, Transition
import OpenOPC


class OPC_Connect(object):

    def __init__(self):
        self.client = self.connect_local('OPC.DeltaV.1')


    def connect_local(self, svr_name):

        opc_client = OpenOPC.open_client('localhost')
        opc_client.connect(svr_name)
        return opc_client

    def read(self, PV):
        readvalue = self.client.read(str(PV))
        #print readvalue
        return readvalue

    def write(self, PV, SP):
        writevalue = self.client.write((str(PV), float(SP)))
        print writevalue
        return writevalue


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
        self.param = tokens[0]
        self.value = tokens[2] # must be a number now
        self.complete = False
        print "Setting", self.param, "value to", self.value, "..."

    def execute(self):
        return self.connection.write(PV = self.param, SP = self.value)

    def iscomplete(self):
        #FIXME: confirm actions: MODE.TARGET to MODE.ACTUAL, SP to PV

        readtup = self.connection.read(self.param)
        readvalue = list(readtup)[0]
        if readvalue == float(self.value):
            self.complete = True
        return self.complete

class TranAttr():
    def __init__(self, tran_attr, connection):
        self.tran_attr = tran_attr
        tokens = split_attr(tran_attr)
        self.connection = connection
        readtup = self.connection.read(PV = tokens[0])
        self.PV = list(readtup)[0]
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
    get_in = diagram.get_state(state_id = in_state)
    in_name = get_in.name
    print "________Testing State::: %r ________" %(in_name)

    destination = get_in.destination  # List of Object
    state_attr = get_in.attrs
    print "substates number:", get_in.num_substates

    #FIXME: substate_num and substates objects empty in StateModel
    ''' Run substate (if any) or execute action'''
    if int(get_in.num_substates) > 0:

        runsub(in_state, diagram)
    elif int(get_in.num_substates) == 0:
        are_complete = list()
        for action in state_attr:
            a = Action(action, connection)
            a.execute() # execute state attribute

            if a.iscomplete():
                are_complete.append(True)
            else:
                are_complete.append(False)


        if False not in are_complete:
            print "... Test on State %r PASS. \n" %(get_in.name)
            transit(in_state, destination, connection)
        else:
            print "... Test on State %r FAIL. \n" %(get_in.name)


def transit(in_state, destination, connection):
    get_in = diagram.get_state(state_id = in_state)
    in_name = get_in.name

    print "Transiting..."

    for dest_state in destination:
        get_dest = diagram.get_state(state_id = dest_state)
        dest_name = get_dest.name

        '''Transition Attribute'''
        tran_attr = diagram.get_transitions(source=in_name, dest=dest_name)
        #FIXME: Transition Attribute always empty, check StateModel.py
        #print "in_state:", in_name, ", dest_state:", dest_name, "have transition:", tran_attr

        reached = list()

        for item in tran_attr:

            if TranAttr(item, connection).verify():
                reached.append(True)
            else:
                reached.append(False)

        if False not in reached:

            #State(name = in_state).deactivate()
            if dest_name != 'END' or []:
                #State(name = dest_state).activate()
                recur(dest_state, diagram, connection)
            elif dest_name == 'END':
                print "===========Test Complete=========="


if __name__ == "__main__":
    from ModelBuilder import StateModelBuilder
    import config, os, time
    from plantUML_state_lexer import get_tokens_from_file
    connection = OPC_Connect()
    time.sleep(3)

    input_path = os.path.join(config.specs_path, 'vpeng', 'Demo_0.0.puml')

    tkns = get_tokens_from_file(input_path)

    builder = StateModelBuilder()
    diagram = builder.parse(tkns)

    print "===========Test Start=========="

    recur(in_state = "[*]", diagram = diagram, connection = connection)

