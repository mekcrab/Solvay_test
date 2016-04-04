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
            print "ERROR: Must pass directed graph instance as first argument"
            raise TypeError

    def set_graph(self, new_graph):
        if not isinstance(new_graph, nx.DiGraph):
            raise TypeError
        else:
            self.graph = new_graph

    def check_path(self, start_node, end_node):
        '''Returns boolean value if path available between given nodes'''
        return nx.has_path(self.graph, start_node, end_node)

    def generate_path_lists(self, start_node, end_node):
        '''method returns a list of all simple paths
                between start_node and end_node'''
        if start_node in self.graph and end_node in self.graph:
            return list(nx.all_simple_paths(self.graph, start_node, end_node))
        else:
            print "ERROR: Specified nodes: start", start_node.name, "end, ", end_node.name, "not found in graph."
            raise NameError

    def generate_path_graphs(self, start_node, end_node):
        '''
        Method returns a subgraph (will be an instance of the same class as current self.graph)
        of all simple paths between start_node and end_node. Note subgraph nodes/edges still reference
        original objects - so changes propegate through all referenced paths!!!
        '''
        subgraphs = list()
        path_list = self.generate_path_lists(start_node, end_node)
        for path in path_list:
            subgraph = self.graph.subgraph(list(path))
            subgraph.remove_edges_from(self.graph.edges())
            # add back only path_edges to cleared subgraph
            for u,v in self.edges_in_path(path):
                subgraph.add_edge(u, v, attr_dict=self.graph.get_edge_data(u,v))
            subgraphs.append(subgraph)
        return subgraphs

    @staticmethod
    def edges_in_path(path):
        '''
        Generates a list of edges from a given path. Utility function to produce subgraphs from generate_path_lists.
        :param path:
        :return:
        '''
        # path is topologically ordered as list (start --> end)
        e = [(path[n], path[n+1]) for n in range(len(path) - 1)]
        return e

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

    def draw_graph(self, output='solver_graph.svg'):
        '''Draws the solver's current graph via pygraphviz using dot layout'''
        if output.split('.')[-1] != 'svg':
            output = '.'.join([output, 'svg'])
        A = nx.nx_agraph.to_agraph(self.graph)
        A.layout(prog='dot')
        A.draw(output)

if __name__ == "__main__":

    # add testing here
    pass


