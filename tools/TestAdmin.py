__author__ = 'vpeng'

from serverside.OPCclient import OPC_Connect, OPCdummy

class TestAdmin():
    def __init__(self, diagram, connection):
        self.diagram = diagram
        self.connection = connection

    def recur(self, in_state):
        state = d.get_state(state_id = in_state)
        self.next_states = state.destination # List of Object
        num_attributes = len(state.attrs)

        print "______________Testing State ::: %r ____________" %(state.name)
        print "Attribute Number:", num_attributes
        complete_count = 0

        # As long as attributes in state not all complete, it will keep attempting to execute until all complete.
        x = 0
        complete = [False] * len(state.attrs)
        while complete_count != num_attributes:
            for x in range(0, len(state.attrs)):
                # TODO: state_attr.set_read_hook(connection.read)
                # TODO: state_attr.set_write_hook(connection.write)
                state_attr = state.attrs[x]
                if not complete[x]:
                    print "Executing Attribute:", state_attr
                    complete[x] = state_attr.execute()
                    print "is_complete:", complete[x]
                else:
                    print "Attribute:", state_attr
                    print "is_complete:", complete[x]

                complete_count = complete.count(True)

            print "Complete Count:", complete_count
        if complete_count == num_attributes:
            return True

    def transit(self, source, destination):
        source = self.diagram.get_state(state_id = source)
        destination = self.diagram.get_state(state_id = destination)

        transitions = self.diagram.get_transitions(source = source.name, dest = destination.name)
        num_attributes = len(transitions)

        complete_count = 0
        while complete_count != num_attributes:
            for transition in transitions:
                for tran_attr in transition.attrs:
                    # TODO: tran_attr.set_read_hook(connection.read)
                    is_complete = tran_attr.execute()
                    while not is_complete:
                        print "Executing Transition:", tran_attr
                        is_complete = tran_attr.execute()
                    if is_complete:
                        complete_count += 1

                    if complete_count == num_attributes:
                        #Activate all State Attributes in Destination State
                        for dest_attr in destination.attrs:
                            dest_attr.activate()
                        return True


class Test(TestAdmin):

    def __init__(self, diagram, connection):
        self.diagram = diagram
        self.connection = connection
        TestAdmin.__init__(self, diagram, connection)
        #TODO: need to make the state_id constant.
        self.start_state = diagram.get_state(state_id = 'state0')

    def start(self):
        print "===========================Test Start========================"
        in_state = self.start_state
        while in_state and TestAdmin(self.diagram, self.connection).recur(in_state):
            next_states = in_state.destination # A List of Possible Destination
            if next_states: # not empty
                print "transiting..."
                for next_state in next_states:
                    print "next_state:", next_state.name
                    if TestAdmin(self.diagram, self.connection).transit(source = in_state, destination = next_state):
                        print "new state:", next_state.name
                        in_state = next_state
            else:
                print "==============================Test Complete========================="
                in_state = next_states


if __name__ == "__main__":

    #from ModelBuilder import StateModelBuilder
    import config, os, time
    #from PlantUML_Lexer import get_tokens_from_file
    import AttrTest

    connection = OPC_Connect()
    time.sleep(1)

    #input_path = os.path.join(config.specs_path, 'vpeng', 'Demo_3.0.puml')

    #tkns = get_tokens_from_file(input_path)

    #builder = StateModelBuilder()
    #diagram = builder.parse(tkns)
    d = AttrTest.make_state_diagram(s = 5)
    print "State Number:", len(d.state_names)
    print "Transition Number:", len(d.transitions)

    Test(diagram = d, connection = connection).start()
