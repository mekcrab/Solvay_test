__author__ = 'vpeng'

from serverside.OPCclient import OPC_Connect

class TestAdmin():
    def __init__(self, diagram, connection):
        self.diagram = diagram
        self.connection = connection

    def recur(self, in_state):
        state = self.diagram.get_state(state_id = in_state)
        self.next_states = state.destination # List of Object
        num_attributes = len(state.attrs)

        print "______________Testing State ::: %r ____________" %(state)
        for state_attr in state.attrs:
            state_attr.set_read_hook(connection.read)
            state_attr.set_write_hook(connection.write)

            state_attr.execute()
            complete_count = 0
            if state_attr.is_complete:
                complete_count += 1
                state_attr.deactivate()

            if complete_count == num_attributes:
                return True

    def transit(self, source, destination):
        source = self.diagram.get_state(state_id = source)
        destination = self.diagram.get_state(state_id = destination)

        transitions = self.diagram.get_transitions(source = source.name, dest = destination.name)
        num_attributes = len(transitions)

        for tran_attr in transitions:
            tran_attr.set_read_hook(connection.read)
            tran_attr.execute()
            complete_count = 0
            if tran_attr.is_complete:
                complete_count += 1

            if complete_count == num_attributes:
                #Activate all State Attributes in Destination State
                for dest_attr in destination.attrs:
                    dest_attr.activate()
                return True


class Test(TestAdmin):

    def __init__(self, diagram, connection):
        TestAdmin.__init__(self, diagram, connection)
        self.start = self.diagram.get_state(state_id = 'START')

    def start(self):
        print "===========Test Start=========="
        in_state = self.start
        while TestAdmin(diagram, connection).recur(in_state) and in_state != '':
            next_states = in_state.destination # A List of Possible Destination
            for next_state in next_states:
                if TestAdmin(diagram, connection).transit(source = in_state, destination = next_state):
                    in_state = next_state
                else:
                    continue


if __name__ == "__main__":

    from ModelBuilder import StateModelBuilder
    import config, os, time
    from PlantUML_Lexer import get_tokens_from_file

    connection = OPC_Connect()
    time.sleep(1)

    input_path = os.path.join(config.specs_path, 'vpeng', 'Demo_3.0.puml')

    tkns = get_tokens_from_file(input_path)

    builder = StateModelBuilder()
    diagram = builder.parse(tkns)

    Test(diagram.flatten_graph, connection).start()
