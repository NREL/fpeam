# -*- coding: utf-8 -*-
import networkx as nx
from networkx.algorithms.shortest_paths.weighted import bidirectional_dijkstra

from FPEAM import utils
LOGGER = utils.logger(name=__name__)


class Router(object):
    """Discover routing between nodes"""

    def __init__(self, edges, node_map, algorithm=bidirectional_dijkstra):
        """

        :param edges: [DataFrame]
        :param node_map: [DataFrame]
        :param algorithm: [function]
        :return:
        """

        self.edges = edges
        self.node_map = node_map

        self.algorithm = algorithm

        self.routes = None
        self.Graph = nx.Graph()

        _ = list(map(lambda x: self.Graph.add_edge(**x), self.edges, ))

    def get_route(self, from_fips, to_fips):
        """
        Find route from <from_fips> to <to_fips>, if exists.

        :param from_fips: [str]
        :param to_fips: [str]
        :return: [DataFrame]
        """

        _from_node = self.node_map[from_fips]
        _to_node = self.node_map[to_fips]

        _route = self.algorithm(self.Graph, _from_node, _to_node)

        return _route


if __name__ == '__main__':
    import sys
    sys.path.append('~/src/fpeam')
    import FPEAM

    from FPEAM import Data

    r = Router(edges=Data.TransportationGraph(fpath='../data/inputs/transportation_graph.csv'),
               node_map=Data.CountyNode(fpath='../data/inputs/counts_node.csv'))
    r.get_route(from_fips='01001', to_fips='01003')
