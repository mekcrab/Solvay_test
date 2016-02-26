__author__ = 'ekopache'

# requires python-requests
import networkx as nx
from GephiStreamer import Node, Edge, GephiStreamerManager


class GraphVis(GephiStreamerManager):
    '''Class to enable real-time visualization of graph structures'''

    default_node_vis = {}
    default_edge_vis = {}

    def __init__(self, **kwargs):
        '''
        Constructor
        :param args:
        :param kwargs:
                iGephiUrl:  URL of gephi master server
        :return: New GraphVis instance
        '''
        # Networkx graph structure mirrors visualized data
        self.G = nx.Graph()

        # define default visualization properties here
        GraphVis.default_node_vis = kwargs.pop('default_node_vis',
                                               {'red':1, 'size':10})
        GraphVis.default_edge_vis = kwargs.pop('default_edge_vis',
                                               {'red':0.5, 'blue':0.5, 'green':0.5, 'weight':1})

        GephiStreamerManager.__init__(self, **kwargs)

    def send_graph_quick(self, nbunch=None, rbg=(1,0,0)):
        '''Sends a graph to the gephi server'''
        if not nbunch:
            nbunch = self.G.nodes()
        else:
            for n in nbunch not in self.G.nodes():
                self.add_node(n)
        send_graph(self.G.subgraph(nbunch), self, rgb=rbg)

    def set_node(self, node_id, realtime=True, node_attrs={}):
        '''
        Add a node to the network datastructure.

        kwargs is an optional dictionary of node properties

        If optional parameter <vis_realtime> is True, gephi visualization will be
        automatically updated.'''
        if self.G.has_node(node_id):
            if node_attrs:
                self.update_node_data(node_id, node_attrs)
            else:
                node_attrs=self.G.node[node_id]
        else:
            # note: here we add node to data graph (visual added below)
            self.G.add_node(node_id, node_attrs)

        # create GephiStreamer.Node instance to send
        # typecast node_id to string
        new_node = Node(str(node_id), **GraphVis.default_node_vis)
        self.add_node(new_node)

        # values from node_attrs override node_vis_props
        # ['r', 'g', 'b'] for node colors except on init --> ['red', 'green', 'blue']
        new_node.property.update(node_attrs)
        self.change_node(new_node)

        if realtime:
            self.commit()

        return new_node

    def add_node_property(self, node_id, property_name, property_val):
        '''Adds a property to a node'''
        self.G.node[node_id][property_name] = property_val

    def update_node_data(self, node_id, node_attrs):
        '''
        Sends an update of node data identified by node_id.
        Node will be added to self.G if not already in graph.
        '''
        self.G.node[node_id] = node_attrs

    def set_edge(self, node1_id, node2_id, realtime=True, edge_attrs={}):
        '''Add a an edge to the visualized graph. Nodes that do not
            exist in the current graph data structure (i.e. NetworkX graph)
            will be automatically created.

            If optional parameter <vis_realtime> is True, gephi visualization will
            be automatically updated.

            "If you define twice a node, it won't do anything.
             If you define an edge with a node that doesn't exist, it won't do anything.
             If you update a node that doesn't exist, it won't do anything.
                -Koumin"
        '''
        if self.G.has_edge(node1_id, node2_id) and edge_attrs:
            self.update_edge_data(node1_id, node2_id, edge_attrs=edge_attrs)
        else:
            self.G.add_edge(node1_id, node2_id, edge_attrs)

        # add node to graphif it does no exist in graph
        n1_vis = self.set_node(node1_id, realtime=False)
        n2_vis = self.set_node(node2_id, realtime=False)

        # Edge(source, target, is_directed)
        new_edge = Edge(n1_vis, n2_vis, False, **GraphVis.default_edge_vis)

        self.add_edge(new_edge)

        # update visualization edge properties
        new_edge.property.update(edge_attrs)
        self.change_edge(new_edge)

        if realtime:
            self.commit()

        return new_edge

    def add_edge_property(self, node1_id, node2_id, property_name, property_val):
        '''Adds a property to an edge'''
        self.G[node1_id][node2_id][property_name] = property_val

    def update_edge_data(self, node1_id, node2_id, edge_attrs={}):
        '''Sends an update of edge data between node1_id and node2_id'''
        self.G.edge[node1_id][node2_id] = edge_attrs

    def clear_visualization(self, clear_data=False):
        for node_id in self.G.nodes():
            self.delete_node(Node(node_id))
            if clear_data:
                self.G.remove_node(node_id)
        self.commit()

    def reset_visualization(self):
        '''Flushes current graph and updates with data in self.G'''
        self.clear_visualization()
        self.send_graph_quick()


def make_gephi_nodes(nbunch, rgb=(1,0,0), size=10, label_fcn = str):
    '''Creates nodes specific to gephi from a list of node identifiers
    Note: networkx note can be any hashable types

    Visual properties available are:
    (x,y,z) integer - position
    (r,g,b) float[0,1] - color
    color string ("0xcccccc") - color alternative to rgb
    size interger - size of node on graph
    '''

    red, green, blue = rgb
    gephi_node_dict = {x:Node(label_fcn(x), red=red, green=green, blue=blue, size=size)
            for x in nbunch}
    return gephi_node_dict


def send_graph(G, gs, rgb=(1,0,0), label_fcn = None):
    '''
    Sends the networkX graph, G, to gephi as a JSON stream
    :param: G   graph to send
    :param: gs  GraphVis instance
    :param: rgb node color
    :param: id_fcn  function to generate node label
    '''

    gnodes = make_gephi_nodes(G.nodes(), rgb=rgb, size=10)

    for k,v1 in gnodes.items():
        gs.add_node(v1)
        try:
            for v2 in make_gephi_nodes(G[k].keys()).values():  # G[k] is networkx node neighbor dictionary
                gs.add_node(v2)
                gs.add_edge(Edge(v1, v2, False, weight=1))
            gs.commit()
        except Exception, e:
            print "Unable to add", k
            print e

    print "Graph sent"
    return gnodes

# quick and dirty setup/testing
if __name__ == "__main__":
    import scratchpad

    G = scratchpad.load_fhx_graph('R-3')

    gs=GephiStreamerManager(iGephiUrl='Tannhauser:8080')

    send_graph(G, gs)
