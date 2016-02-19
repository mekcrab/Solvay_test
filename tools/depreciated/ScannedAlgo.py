'''
Module contains definitions for constructing graphs of finite algorithms.
Intended to be evaluated in discrete time at a specified scan rate.

Can alternatively be viewed as a two-state system: executing/not executing

Examples:
    DeltaV fuction block diagrams
    PROVOX function state tables
    PLC ladder logic
'''

__author__ = 'erik.kopache'

from networkx.classes.digraph import DiGraph

class Data(object):
    '''Base class for all data objects'''
    def __init__(self, data_id, *args, **kwargs):
        self.id = data_id   # namespace-unique id for this data
        self.value = kwargs.pop('value', None)   # current value of the data
        self.type = kwargs.pop('type', type(self.value))

    def get_value(self):
        return self.value

    def set_value(self, new_value):
        self.value = new_value

    def is_valid(self):
        '''
        Returns an evaluation of the validity of the data value.
        Based on type checking, OPC status parameter, etc as defined in the subclass
        '''
        raise NotImplementedError


class PersistentData(Data):
    '''
    Memory component which retains value between execution ('scans') of the algorithm.
    Ex. register or
    '''
    def __init__(self, data_id, *args, **kwargs):
        Data.__init__(self, data_id, args, kwargs)


class XputData(Data):
    '''
    External data either (1) as an input to the algorithm or (2) as an output
    As a graph node:
        input data will have only outgoing edges
        output data only incoming edges
    '''
    def __init__(self, data_id, *args, **kwargs):
        Data.__init__(self, data_id, args, kwargs)


class Function(object):
    '''
    executes one or more times in completion of the algorithm, operating on PersistentData
    '''
    def __init__(self, function_id, *args, **kwargs):
        '''Constructor'''
        self.id = function_id
        self.expression = kwargs.pop('expression', None)  # None type represents the identity function

    def execute(self):
        '''
        Returns value of function output, given required inputs.
        To be defined by subclassing.
        '''
        raise NotImplementedError


class ScannedAlgorithm(DiGraph):
    '''
    Algorithm which operates one or more PersistentData/Inputs[XputData],
    yielding either an Output[XputData] or transformed PersistentData

    Nodes represent data
    Edges represent data manipulation (read, write, transformation, calculation, etc.)
    '''

    def __init__(self, algo_id, *args, **kwargs):
        DiGraph.__init__(self, args, kwargs)
        self.id = algo_id
        self.scan_count = 0
        self.input_data = []
        self.output_data =[]
        self.data_id_dict = {}  # internal dictionary for lookups of data nodes by id
        self.scan_rate = kwargs.pop('scan_rate')  # rate at which module should be scanned

    def add_data(self, data_object):
        '''Adds a single data node to the graph. Data can be embedded ScannedAlgorithms'''
        if not (isinstance(data_object, Data) or isinstance(data_object, ScannedAlgorithm)):
            raise TypeError
        self.add_node(data_object, attr_dict=data_object.__dict__)
        self.data_id_dict[data_object.id] = self.node[data_object]

    def add_function(self, function_object, input_id, output_id):
        '''Adds a function linking data objects'''
        if not isinstance(function_object, Function):
            raise TypeError
        self.add_edge(self, input_id, output_id, attr_dict=function_object.__dict__)

    def get_node_by_id(self, node_id):
        return self.node[self.data_id_dict[node_id]]

    def find_inputs(self):
        '''Determines input data - i.e. nodes with in_degree = 0'''
        self.input_data = [node for node, in_degree in self.in_degree() if in_degree==0]

    def find_outputs(self):
        '''Determines output data - i.e. nodes with out_degree = 0'''
        self.output_data = [node for node, out_degree in self.out_degree() if out_degree==0]

    def evaluate(self):
        '''
        Updates all Data in the algorithm, simulating a single scan.
        Input data must be updated by external source, if appplicable
        '''
        # start with inputs, evaluate one succession level at a time until all nodes have been visited
        pass