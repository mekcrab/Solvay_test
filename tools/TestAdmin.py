__author__ = 'vpeng'

from serverside.OPCclient import OPC_Connect
import time


from Utilities.Logger import LogTools
dlog = LogTools('TestAdmin.log', 'TestAdmin')
dlog.rootlog.warning('TestAdmin initialized')

def remove_duplicates(values):
    cleanup = set(values)
    return list(cleanup)


class TestAdmin():
    def __init__(self, diagram, connection, poll_interval=0.5, timeout=600):
        self.diagram = diagram
        self.connection = connection
        self.logger = dlog.MakeChild('TestAdmin')
        self.poll_interval = poll_interval  # interval between calls to execute states or transitions
        self.global_timeout = timeout  # global timeout if all states not achieved

    def recur(self, in_state):
        state = self.diagram.get_state(state_id=in_state)
        num_attributes = len(state.attrs)
        complete_count = 0

        # set read/write hooks for all attributes
        [(attr.set_read_hook(connection.read), attr.set_write_hook(connection.write)) for attr in state.attrs]

        self.logger.debug("Testing state::: %r, %r attribute(s) found", state.name, num_attributes)

        mark_timeout = time.time()
        # As long as (not any state.attrs.complete), keep attempting attr.execute at specified polling interval
        while 1:
            poll_time = time.time() + self.poll_interval

            # (1) execute test loop if all attributes are not complete
            # each attribute is executed during every polling period -- in case the value changes!!
            # TODO - find out how long attr.execute() method takes for each attribute type (see timeit)
            for attr in state.attrs:
                try:
                    complete_count += attr.execute()
                except TypeError:
                    self.logger.error('Error in %r.execute()', attr)
                    continue

            # (2) look at results
            #   (a) check if all attributes have passed,
            if complete_count == num_attributes:
                return True
            #  (b)  or the state has timed out...
            elif (time.time() - mark_timeout) > self.global_timeout:
                return False  # or other timeout logic here!!
            #  (c) otherwise wait for the next polling interval
            else:
                complete_count = 0
                while time.time() < poll_time:
                    pass

    def transit(self, source, destination):
        source = self.diagram.get_state(state_id=source)
        destination = self.diagram.get_state(state_id=destination)

        transitions = self.diagram.get_transitions(source=source.name, dest=destination.name)
        num_attributes = len(transitions[0].attrs)

        complete_count = 0
        # FIXME: empty transition on the diagram is built as one item in the transition list as well.
        if num_attributes == 0:
            return True
        else:
            while complete_count != num_attributes:
                self.logger.debug("Testing transition between source state %r and destination state %r",
                                  source.name, destination.name)
                for transition in transitions:
                    for tran_attr in transition.attrs:
                        # TODO: tran_attr.set_read_hook(connection.read)
                        tran_attr.set_read_hook(connection.read)
                        tran_attr.set_write_hook(connection.write)
                        is_complete = tran_attr.execute()
                        while not is_complete:
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

        for state in diagram.state_names:
            state = diagram.get_state(state)
            if len(state.source) == 0:
                self.start_state = state
        # self.start_state = diagram.get_state(state_id = 'START')

    def start(self):
        self.logger.debug("Start Testing Diagram::: %r", diagram.id)
        in_state = self.start_state
        while in_state and TestAdmin(self.diagram, self.connection).recur(in_state):
            # FIXME: remove duplicated sources/destinations in TestSolver/ModelBuilder
            next_states = remove_duplicates(in_state.destination) # A List of Possible Destination
            if next_states: # not empty
                print "transiting..."
                # FIXME: Get all transitions evaluate at the runtime because of multiple detinations. Maybe it can be solved in the TestSolver.
                transition_pass = False
                while transition_pass != True:
                    for next_state in next_states:
                        print "next_state:", next_state.name
                        transition_pass = TestAdmin(self.diagram, self.connection).transit(source = in_state, destination = next_state)
                        in_state = next_state
            else:
                print "==============================Test Complete========================="
                in_state = next_states


if __name__ == "__main__":

    from ModelBuilder import build_state_diagram
    import config, os, time
    from Attributes import AttributeBuilder
    from pprint import pprint as pp

    connection = OPC_Connect()
    time.sleep(1)

    input_path = os.path.join(config.specs_path, 'vpeng', 'AttrTest_0.0.puml')

    # create attribute builder instance for solving attributes
    #abuilder = AttributeBuilder.create_attribute_builder(server_ip='127.0.0.1', server_port=5489)
    abuilder = AttributeBuilder.create_attribute_builder(server_ip='10.0.1.200', server_port=5489)

    # ==Build diagram, preprocessor optional==:
    diagram = build_state_diagram(input_path, attribute_builder=abuilder, preprocess=True)

    print "Parsed", len(diagram.state_names.values()), "states"
    print "Parsed", len(diagram.get_transitions()), "transitions"

    print "Attributes generated:"
    pp(diagram.collect_attributes())

    Test(diagram=diagram, connection=connection).start()
