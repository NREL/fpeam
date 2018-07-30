# -*- coding: utf-8 -*-
import networkx as nx
from networkx.algorithms.shortest_paths.weighted import bidirectional_dijkstra

from FPEAM import utils
LOGGER = utils.logger(name=__name__)


class Router(object):
    """Discover routing between nodes"""

    def __index__(self, edges, node_map, algorithm=bidirectional_dijkstra):
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

        _from_node = None
        _to_node = None

        return self.algorithm(self.Graph, _from_node, _to_node)
