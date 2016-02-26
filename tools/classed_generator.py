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
    def __init__(self, tran_attr, connection): # input should a single tran_attr tuple (..,..,..)
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
            print "Transition of %r FAIL" %(self.tran_attr)

        return self.reached


class execute():
    def __init__(self, diagram, connection):
        self.diagram = diagram
        self.connection = connection

    def runsub(self, parent):
        self.parent = parent
        get_parent = diagram.get_state(state_id = parent)
        self.parentdest = get_parent.destination
        substates = get_parent.substates
        for substate in substates:
            sub = diagram.get_state(state_id = substate)
            subsource = sub.source
            subdest = sub.destination
            if subsource == []: # This substate = Start
                #State(name = substate).activate()
                #print "\nActivating state %r: %r" %(substate.name, substate.active)
                self.recur(in_state = substate)

    def recur(self, in_state):
        get_in = diagram.get_state(state_id = in_state)
        in_name = get_in.name
        substates = get_in.substates

        print "________Testing State::: %r ________" %(in_name)
        num_substates = len(substates)
        destination = get_in.destination  # List of Object
        state_attr = get_in.attrs
        print "substates number:", num_substates

        ''' Run substate (if any) or execute action'''
        if int(num_substates) > 0:
            print "*Substate(s) found in state: %r. \n*Start running substates below:" %(in_name)
            self.runsub(in_state)
        elif int(num_substates) == 0:
            are_complete = list()
            for action in state_attr:
                a = Action(state_attr = action, connection = self.connection)
                a.execute() # execute state attribute

                if a.iscomplete():
                    are_complete.append(True)
                else:
                    are_complete.append(False)


            if False not in are_complete:
                print "... Test on State %r PASS. \n" %(get_in.name)
                self.transit(in_state, destination)
            else:
                print "... Test on State %r FAIL. \n" %(get_in.name)


    def transit(self, source, destination):
        get_source = diagram.get_state(state_id = source)
        source_name = get_source.name

        #TODO: Need to add 'parent' property in StateModel: in_state.parent != None
        if destination == []: # End of Substates
            print "*Test for substate(s) in state: %r complete" %(self.parent.name)
            self.transit(self.parent,self.parentdest)
        else:
            print "Transiting......"

            for dest_state in destination:
                get_dest = diagram.get_state(state_id = dest_state)
                dest_name = get_dest.name

                '''Transition Attribute'''
                tran_list = diagram.get_transitions(source=source_name, dest=dest_name) # List of transition attrs

                reached = list()
                for tran_attr in tran_list:
                    tran_attr = tran_attr.attrs
                    #print "in_state:", source_name, ", dest_state:", dest_name, "have transition:", tran_attr

                    for item in tran_attr:
                        print "Verifying:", item

                        if TranAttr(tran_attr = item, connection = self.connection).verify():
                            reached.append(True)
                        else:
                            reached.append(False)

                    if False not in reached:

                        #State(name = get_source).deactivate()
                        #print "\nState %r deactivated: %r" %(source_name, not get_source.active)
                        if dest_name != 'END':
                            #State(name = get_dest).activate()
                            #print "Activating state %r: %r\n" %(dest_name, get_dest.active)
                            self.recur(dest_state)

                        elif dest_name == 'END':
                            print "===========Test Complete=========="


if __name__ == "__main__":
    from ModelBuilder import StateModelBuilder
    import config, os, time
    from PlantUML_Lexer import get_tokens_from_file
    connection = OPC_Connect()
    time.sleep(1)

    input_path = os.path.join(config.specs_path, 'vpeng', 'Demo_2.0.puml')

    tkns = get_tokens_from_file(input_path)

    builder = StateModelBuilder()
    diagram = builder.parse(tkns)

    print "===========Test Start=========="

    exe = execute(diagram = diagram, connection = connection)

    exe.recur(in_state = "[*]")

