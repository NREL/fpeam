import networkx as nx
import   pandas as pd
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

        LOGGER.debug('loading routing graph')
        _ = self.edges.apply(lambda x: self.Graph.add_edge(**x), axis=1)

    def get_route(self, from_fips, to_fips, from_node=None, to_node=None):
        """
        Find route from <from_fips> to <to_fips>, if exists.

        :param from_fips: [str]
        :param to_fips: [str]
        :param from_node: [int]
        :param to_node: [int]
        :return: [DataFrame]
        """

        if not from_node:
            try:
                from_node = self.node_map.loc[from_fips].node_id
            except KeyError:
                LOGGER.error('FIPS code %s not found in FIPS to node lookup' % (from_fips, ))

        if not to_node:
            try:
                to_node = self.node_map.loc[to_fips].node_id
            except KeyError:
                LOGGER.error('FIPS code %s not found in FIPS to node lookup' % (to_fips, ))

        if not from_node and to_node:
            raise ValueError('start or end node is undefined')

        _path = self.algorithm(self.Graph, from_node, to_node)[1]

        _route = pd.DataFrame(_path, columns=['start_node'], dtype=int)
        _route['end_node'] = _route['start_node'].shift(-1)
        _route = _route[:-1]
        _route['end_node'] = _route['end_node'].astype(int)

        _edges = _route.apply(lambda x: self.Graph.get_edge_data(u=x.start_node,
                                                                 v=x.end_node)['edge_id'], axis=1)

        _summary = self.edges.loc[self.edges.edge_id.isin(_edges.values) &
                                  ~self.edges.countyfp.isna() &
                                  ~self.edges.statefp.isna()][['edge_id',
                                                               'statefp',
                                                               'countyfp',
                                                               'weight',
                                                               'fclass']].groupby(['statefp',
                                                                                   'countyfp',
                                                                                   'fclass'])\
            .sum().reset_index()

        _summary['region_transportation'] = _summary['statefp'] + _summary['countyfp']
        _summary['vmt'] = _summary['weight'] / 1000.0 * 0.621371

        return _summary[['region_transportation', 'vmt']]
