__author__ = 'erik'

import networkx as nx

class GraphSolver(object):
    '''
    Class for providing various path solutions for
        directed graphs. Applications in flow control and
        test case generation.
    '''

    def __init__(self, original_graph):
        self.graph = original_graph

    def set_graph(self, graph):
        if not isinstance(graph, nx.Digraph):
            raise TypeError
        else:
            self.graph = graph

    def generate_paths(self, start_node, end_node):
        '''method returns a list of all simple paths
                between start_node and end_node'''
        if start_node in self.graph and end_node in self.graph:
            return list(nx.all_simple_paths(self.graph, start_node, end_node))
        else:
            print "Specified nodes: start", start_node, "end, ", end_node, "not found in graph"
            raise NameError

