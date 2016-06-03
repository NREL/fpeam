# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 1:02:31 2016

Populates tables for logistics emissions and electricity consumption associated with feedstock processing

Inputs include:
    list of feedstock types (feedstock_list)
    container (cont)

@author: aeberle
"""

import SaveDataHelper
from utils import config, logger


class Logistics(SaveDataHelper.SaveDataHelper):
    """
    Computes the emissions and electricity use associated with feedstock processing
    Only emissions are VOC from wood drying (forestry only)
    Electricity is tabulated to compute total kWh by feedstock type
    """

    def __init__(self, feedstock_list, cont):
        """

        :param feedstock_list: list of feedstocks to process
        :param cont: Container object
        :return:
        """
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.feedstock_list = feedstock_list
        self.document_file = "Logistics"  # gets used to save query to a text file for debugging purposes
        self.electricity_per_dt = config.get('electricity_per_dt')  # electricity dictionary

        self.kvals = cont.get('kvals')

        # get dictionary for production column names
        self.column_dict = config.get('prod_column_dict')

        # dictionary for VOC emission factor from wood drying
        self.voc_wood_ef = config.get('voc_wood_ef')

        # set feedstock id table for transportation data
        self.transport_feed_id_dict = config.get('feed_id_dict')

        # get dictionaries for transportation data tables
        self.feed_type_dict = config.get('feed_type_dict')  # dictionary of feedstock types
        self.transport_table_dict = config.get('transport_table_dict')

        # get yield type for scenario
        self.yield_type = config.get('yield')

    def electricity(self, feed, logistics, yield_type):
        """
        Tally electricity consumption from feedstock processing
        Update logistics table with these values

        Equation for computing electricity consumption (generated by Ethan Warner):

        E = B * electricity_per_dt

        E = electricity (kWh per year per county)
        B = biomass production (dry short ton per yr per county)
        electricity_per_dt = electricity consumed (kWh per dry short ton?

        :param yield_type: yield type for scenario
        :param run_code: run code associated with NONROAD run
        :param logistics: logistics type being evaluated
        :return: True if update query is successful, False if not
        """

        # set feedstock name
        self.kvals['feed'] = feed.lower()

        # set feedstock id name for transportation table
        self.kvals['feed_id'] = self.transport_feed_id_dict[feed]

        # set transport table name
        self.kvals['transport_table'] = self.transport_table_dict[self.feed_type_dict[feed]][yield_type][logistics] + '_%s' % (config.get('year_dict')[feed])

        logger.debug('Calculating electricity consumption for {feed}'.format(feed=feed))

        # set electricity consumption factor using feedstock type
        self.kvals['electricity_per_dt'] = self.electricity_per_dt[feed][logistics]

        # set logistics type
        self.kvals['logistics'] = logistics

        # set yield type
        self.kvals['yield_type'] = yield_type

        # generate string for query
        query = """ INSERT INTO {scenario_name}.processing (fips, feed, electricity, logistics_type, yield_type)
                    SELECT transport_data.sply_fips, '{feed}', transport_data.used_qnty * {electricity_per_dt}, '{logistics}', '{yield_type}'
                    FROM {production_schema}.{transport_table} transport_data
                    WHERE transport_data.used_qnty > 0.0 AND transport_data.feed_id = '{feed_id}'
                   ;""".format(**self.kvals)

        # execute query
        return self._execute_query(query)

    def voc_wood_drying(self, run_code, logistics, yield_type):
        """
        Compute VOC emissions from wood drying
        Only applies to forestry

        Equation for computing VOC emissions from wood drying (generated by Ethan Warner):

        VOC = (B * a) * (VOC_ef_hammermill + VOC_ef_dryer) / b

        VOC = VOC emissions (metric tons per year per county)
        B = biomass production (dry short ton per yr per county)
        a = constant (0.9071847 metric tons per short ton)
        VOC_ef_h = emission factor for VOC from hammer mill (kg per dry metric ton of feedstock)
        VOC_ef_d = emission factor for VOC from grain dryer (kg per dry metric ton of feedstock)
        b = constant (1000 kg per metric ton)

        :param yield_type: type of yield used for scenario
        :param run_code: run code for feedstock type
        :param logistics: logistics type being evaluated
        :return: True if update query is successful, False if not
        """

        logger.info('Computing VOC emissions from wood drying')

        # set feedstock id
        feed = run_code[0:2]

        # set dictionary values for string formatting
        kvals = {
                 'transport_table': self.transport_table_dict[self.feed_type_dict[feed]][yield_type][logistics],  # transport table
                 'run_code': run_code,  # run code
                 'feed': feed,  # feedstock id
                 'feed_name': self.transport_feed_id_dict[feed],  # name of feedstock
                 'logistics': logistics,  # logistics type
                 'yield_type': yield_type,  # yield type
                 'a': 0.9071847,  # metric ton per short ton
                 'b': 1000.0,  # kg per metric ton
                 'VOC_ef_h': self.voc_wood_ef[logistics]['hammer_mill'],  # VOC emission factor for hammer mill
                 'VOC_ef_d': self.voc_wood_ef[logistics]['grain_dryer'],  # VOC emission factor for grain dryer
                 'scenario_name': self.kvals['scenario_name'],
                 'production_schema': self.kvals['production_schema'],
                 'year': config.get('year_dict')['all_crops']
                 }

        # generate string for query and append to queries
        query = """UPDATE {scenario_name}.processing process
                LEFT JOIN {production_schema}.{transport_table}_{year} transport_data ON process.fips = transport_data.sply_fips
                SET voc_wood = transport_data.used_qnty * {a} * ({VOC_ef_h} + {VOC_ef_d}) / {b}
                WHERE   logistics_type = '{logistics}' AND
                        yield_type = '{yield_type}'
                        AND feed = '{feed}'
                        AND feed_id = '{feed_name}';""".format(**kvals)

        return self._execute_query(query)

    def calc_logistics(self, logistics_list):
        # Execute wood drying and electricity functions for all feedstocks in feedstock list
        logger.info('Evaluating logistics')

        for feed in self.feedstock_list:
            if self.transport_feed_id_dict[feed] != 'None':
                for logistics_type in logistics_list:
                    # compute electricity
                    self.electricity(feed, logistics_type, self.yield_type)

                    if feed.startswith('F'):
                        self.voc_wood_drying(feed, logistics_type, self.yield_type)

