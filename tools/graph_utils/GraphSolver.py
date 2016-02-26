__author__ = 'erik'

import networkx as nx

class GraphSolver(object):
    '''
    Class for providing various path solutions for
        directed graphs. Applications in flow control and
        test case generation.
    '''

    def __init__(self, original_graph):
        if isinstance(original_graph, nx.DiGraph):
            self.graph = original_graph
        else:
            print "Must pass directed graph instance as first argument"
            raise TypeError

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

    def calculate_complexity(self):
        '''
        Calculates cyclomatic compexity of graph according to McCabe (1976) - A Complexity Measure
        v(G) = e - n + p
            where:
                v(G)    cyclomatic complexity
                e       number of edges
                n       number of nodes
                p       number of connected components

        It is assumed that ending nodes can loop back to starting nodes by re-execution of the program, thus the graph
         is assumed to always be strongly connected.

        Note: v(G) is the size of the basis set of the graph - i.e. maximum number of linearly independent paths in G
        '''
        return self.graph.number_of_edges() - self.graph.number_of_nodes() + \
                                                nx.number_weakly_connected_components(self.graph)


