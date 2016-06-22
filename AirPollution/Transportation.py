# -*- coding: utf-8 -*-
"""
Created on Thur Mar 3 9:24:46 2016

Populates tables for transportation emissions associated with off-farm transport

Inputs include:
    feedstock name (feed)
    container (cont)
    fips code (fips)
    vehicle miles travelled (vmt)
    population, or number, of vehicles (pop)
    silt data (s)

@author: aeberle
"""

import SaveDataHelper
from utils import config, logger


class Transportation(SaveDataHelper.SaveDataHelper):
    """
    Computes the emissions associated with off-farm transportation
    """

    def __init__(self, feed, cont, logistics_type, yield_type):
        """

        :param feed: feedstock to process
        :param cont: Container object
        :param fips: FIPS code
        :param vmt: vehicle miles traveled
        :param pop: popuation of vehicles 
        :param logistics_type: type of logistics system
        :param silt: silt content
        :param yield_type: type of yield considered in scenario
        :param moves_fips: FIPS code for MOVES data (if state-level MOVES run, then different from fips above)
        :return:
        """
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.feed = feed
        self.document_file = "Logistics"  # filename for saving queries to text file for debugging

        self.kvals = cont.get('kvals')

        # set other values in kvals dictionary
        self.kvals['feed'] = feed.lower()  # feedstock name
        self.kvals['year'] = config['year_dict'][self.feed]  # year of scenario run
        self.kvals['g_per_mt'] = 1e6  # number of grams in one metric ton
        self.kvals['logistics_type'] = logistics_type  # type of logistics system
        self.kvals['yield_type'] = yield_type  # type of yield examined

        # set feedstock id for transportation data
        self.transport_feed_id_dict = config.get('feed_id_dict')
        self.kvals['transport_feed_id'] = self.transport_feed_id_dict[self.feed]

        # set truck capacity
        self.truck_capacity = config.get('truck_capacity')
        self.kvals['capacity'] = self.truck_capacity[self.feed][self.kvals['logistics_type']]

        # set name of table for transportation data
        feed_type_dict = config.get('feed_type_dict')  # dictionary of feedstock types
        self.kvals['transport_table'] = config.get('transport_table_dict')[feed_type_dict[feed]][yield_type][logistics_type] + '_%s' % (config['year_dict'][self.feed])

        # get toggle for running moves by crop
        moves_by_crop = config.get('moves_by_crop')

        # set moves database names
        self.kvals['db_out'] = config.get('moves_output_db')  # output database for MOVES run (output database same for all crops)

        # set input database and scenario id depending on moves_by_crop
        if moves_by_crop is False:
            feed = 'all_crops'

        self.kvals['end_moves_scen_id'] = "{crop}_{year}_{month}_{day}".format(crop=feed,
                                                                                day=config.get('moves_timespan')['d'][0],
                                                                                month=config.get('moves_timespan')['mo'][0],
                                                                                year=self.kvals['year'])

        self.kvals['end_db_in'] = "_{year}_{feed}_in".format(feed=feed, year=self.kvals['year'])  # end of string for MOVES input database

        # dictionary of column names for transportation data
        self.transport_column = config.get('transport_column')

        # set the name of the transportation distance column depending on the logistics type
        trans_col = 'c.%s' % (self.transport_column[logistics_type]['dist'], )  # equals dist for conventional
        if logistics_type == 'A':
            trans_col += '+ c.%s' % (self.transport_column[logistics_type]['dist_2'], )  # two columns for advanced

        # set transportation column in kvals
        self.kvals['vmt'] = trans_col

        # dictionary of pollutant names and IDs
        self.pollutant_dict = config.get('pollutant_dict')

        # open SQL connection and create cursor
        self.db = cont.get('db')

    def process_moves_data(self):
        """
        Post-process MOVES outputs to compute total combustion emissions from off-farm transport

        Call function to compute total running emissions per trip
        Call function to compute total start emissions per trip
        Call function to compute total resting evaporative emissions per trip (currently zero)

        Update transportation table with total emissions

        :return:
        """
        logger.info('Post-processing MOVES output for feed: {feed}, logistics: {logistics_type}, yield type: {yield_type}'.format(**self.kvals))

        self.calc_run_emission()
        self.calc_start_hotel_emissions()
        self.calc_rest_evap_emissions()

        query = """UPDATE {scenario_name}.transportation
                   SET    total_emissions = (CASE WHEN run_emissions  = 0 THEN 0
                                                  WHEN run_emissions != 0 THEN (run_emissions + start_hotel_emissions + rest_evap_emissions)
                                             END)
                   WHERE  feedstock      = '{feed}'
                     AND  logistics_type = '{logistics_type}'
                     AND  yield_type     = '{yield_type}'
                   ;""".format(**self.kvals)

        self.db.input(query)

    def calc_run_emission(self):
        """
        Calculate total running emissions per trip (by pollutant)
        Equal to sum(ratePerDistance * vmtfrac_in_speedbin[i] * vmt) for all speed bins, pollutant processes, day types, hours, and road types
        Insert values into transportation table

        :return:
        """

        errors = dict()

        query = """SELECT state FROM {constants_schema}.moves_statelevel_fips_list_{year} ORDER BY state;""".format(**self.kvals)
        state_list = self.db.output(query)[0]

        for state in state_list:
            # set state
            self.kvals['state'] = state[0]
            for key in self.pollutant_dict:
                logger.info('Calculating running emissions for pollutant: %s, state:%s' % (key, state))

                # set pollutant name and ID
                self.kvals['pollutant_name'] = key
                self.kvals['pollutantID'] = self.pollutant_dict[key]

                # @TODO: moves_output_db tables need to be cleaned so there is only one result for each movesid

                query = """INSERT INTO {scenario_name}.transportation (pollutantID, fips, feedstock, yearID, logistics_type, yield_type, run_emissions)
                   SELECT      a.pollutantID
                             , c.sply_fips
                             , '{feed}'
                             , '{year}'
                             , '{logistics_type}'
                             , '{yield_type}'
                             , SUM(a.ratePerDistance * b.avgSpeedFraction) * c.used_qnty / {capacity} * ({vmt}) / {g_per_mt}
                   FROM      {moves_output_db}.rateperdistance          a
                   LEFT JOIN {constants_schema}.averagespeed            b ON (a.roadTypeID = b.roadTypeID AND a.avgSpeedBinID = b.avgSpeedBinID AND a.hourID = b.hourID AND a.dayID = b.dayID)
                   LEFT JOIN {production_schema}.{transport_table}      c ON (a.state = c.state)
                   WHERE     a.MOVESScenarioID_no_fips = '{end_moves_scen_id}'
                     AND     c.feed_id                 = '{transport_feed_id}'
                     AND     a.pollutantID             = '{pollutantID}'
                     AND     a.state                   = '{state}'
                   GROUP BY    a.pollutantID
                             , c.sply_fips
                ;""".format(**self.kvals)

                try:
                    self.db.input(query)
                except Exception, e:
                    errors[key] = e

            [logger.error('Error calculating running emissions for %s: %s' % (key, val)) for key, val in errors.iteritems()]

    def calc_start_hotel_emissions(self):
        """
        Calculate total start and hoteling emissions per trip (by pollutant)
        Equal to sum(output.ratePerVehicle * pop) for all pollutant processes, days, hours, and road types
        Update transportation table with these values
        """

        for key in self.pollutant_dict:
            logger.info('Calculating start emissions for %s' % (key, ))

            # set pollutant name and ID
            self.kvals['pollutant_name'] = key
            self.kvals['pollutantID'] = self.pollutant_dict[key]

            # @TODO: query needs to be parameterized and optimized
            # @TODO: moves_output_db tables need to be cleaned so there is only one result for each movesid
            query = """UPDATE {scenario_name}.transportation tr
                       SET start_hotel_emissions = (SELECT SUM(rv.ratePerVehicle * td.used_qnty / {capacity} / {g_per_mt}) as hotel_emissions
                                                     FROM    {db_out}.ratepervehicle rv
                                                     LEFT JOIN {production_schema}.{transport_table} td
                                                            ON LEFT(td.sply_fips, 2) = LEFT(rv.MOVESScenarioID, 2)
                                                     WHERE rv.MOVESScenarioID = (SELECT CONCAT(fips, '{end_moves_scen_id}')
                                                                                 FROM {constants_schema}.moves_statelevel_fips_list_{year}
                                                                                 WHERE state = LEFT(td.sply_fips, 2))                        AND
                                                           rv.pollutantID = {pollutantID}                                                    AND
                                                           td.feed_id = '{transport_feed_id}'                                                AND
                                                           rv.yearID = '{year}'                                                              AND
                                                           sply_fips = tr.fips
                                                     GROUP BY td.sply_fips, td.feed_id, rv.MOVESScenarioID, rv.pollutatnID, rv.yearID)
                                                     WHERE tr.pollutantID = '{pollutant_name}';""".format(**self.kvals)

            # query = """UPDATE {scenario_name}.transportation
            #            SET    start_hotel_emissions_per_trip = (SELECT   SUM(table1.ratePerVehicle / {g_per_mt}) AS start_hotel_emissions_per_trip
            #                                                     FROM     {db_out}.ratepervehicle table1
            #                                                     WHERE    pollutantID     = {pollutantID}
            #                                                       AND    MOVESScenarioID = '{moves_scen_id}'
            #                                                     GROUP BY yearID, pollutantID
            #                                                    )
            #               WHERE pollutantID    = '{pollutant_name}'
            #                 AND fips           = '{fips}'
            #                 AND feedstock      = '{feed}'
            #                 AND yearID         = '{year}'
            #                 AND logistics_type = '{logistics_type}'
            #                 AND yield_type     = '{yield_type}'
            #            ;""".format(**self.kvals)

            self.db.input(query)

    def calc_rest_evap_emissions(self):
        """
        Calculate total resting evaporative fuel vapor venting rates
        Currently zero because only using 12 hr time span and resting evaporative rates require 24 hr selection
        Also, MOVES assumes that diesel fuel has zero evaporative venting emissions
        """
        logger.warning('Resting evaporative fuel vapor venting rates are zero for diesel fuel')
        logger.warning('If fuel type is not diesel, additional code needs to be written to process fuel vapor evaporative emissions')
        # @TODO: if fuel type changes, then we will need to add code to compute evaporative fuel vapor venting emissions
        pass

    def transport_fugitive_dust(self):
        """
        Compute fugitive dust emissions generated by off-farm transportation

        E_fug_dust = trips * ((c * L_u * k_a * (s / 12) ^ a * (W / 3) ^ b) +
                              (L_s * k_b * sLS ^ 0.91 * W ^ 1.02) / g_per_mt)

        where   E_fug_dust = emissions of fugitive dust (in metric tons)
                c = constant to convert lb to metric ton = 0.000453592 mt/lb
                trips = number of trips determined based on production quantity and truck capacity
                L_u = distance traveled on unpaved roads (mi/load)
                L_s = distance traveled on secondary paved roads (mi/load)
                s = unpaved road surface silt content (%), which varies by state (EPA 2003)
                sLS = secondary paved road silt loading (0.4 g/m^2)
                sLP = primary paved road silt loading (0.045 g/m^2)
                W = average weight of vehicles on the road = 3.2 tons (national estimate used by NEI 2011)
                k_a = particle size multiplier (PM10 = 1.5 lb/mile; PM2.5 = 0.15 lb/mile)
                k_b = particle size multiplier (PM10 = 0.0022 g/mile; PM2.5 = 0.00054 g/mile)
                a = empirical constant = 0.9
                b = empirical constant = 0.45
                g_per_mt = constant to convert from grams to metric tons

        For conventional system:    L_u = dist <= 2 miles
                                    L_s = dist > 2 miles

        For advanced system:        L_u = dist_field_depot <= 2 miles
                                    L_s = dist_field_depot > 2 miles + dist_depot_refinery

        Update transportation table with these values
        """

        logger.info('Calculating fugitive dust emissions for feed: {feed}, logistics: {logistics_type}, yield type: {yield_type}'.format(**self.kvals))

        k_a = dict()
        k_a['PM10'] = 1.5
        k_a['PM25'] = 0.15

        k_b = dict()
        k_b['PM10'] = 0.0022
        k_b['PM25'] = 0.00054
        self.kvals['a'] = 0.9
        self.kvals['b'] = 0.45
        self.kvals['c'] = 0.000453592
        self.kvals['sLS'] = 0.4
        self.kvals['sLP'] = 0.045
        self.kvals['W'] = 3.2
        pm_list = ['PM10', 'PM25']

        for pm in pm_list:
            # set k_a and k_b values for correct pm type
            self.kvals['k_a'] = k_a[pm]
            self.kvals['k_b'] = k_b[pm]
            self.kvals['pollutant_name'] = pm
            if self.kvals['logistics_type'] == 'A':
                self.kvals['dist'] = '(%s + %s)' % (self.transport_column[self.kvals['logistics_type']]['dist'], self.transport_column[self.kvals['logistics_type']]['dist_2'])
            elif self.kvals['logistics_type'] == 'C':
                self.kvals['dist'] = '%s' % (self.transport_column[self.kvals['logistics_type']]['dist'])

            # fugitive dust emissions from unpaved roads
            query_fd = """INSERT INTO {scenario_name}.fugitive_dust (fips, feedstock, yearID, pollutantID, logistics_type, yield_type, unpaved_fd_emissions, sec_paved_fd_emissions, pri_paved_fd_emissions)
                          SELECT      td.sply_fips AS fips,
                                      '{feed}',
                                      '{year}',
                                      '{pollutant_name}',
                                      '{logistics_type}',
                                      '{yield_type}',
                                      ({c} * {k_a} * (uprsm_pct_silt / 12) ^ {a} * ({W} / 3) ^ {b}) * (CASE WHEN {dist} <= 2
                                                                                                         THEN IFNULL(SUM(used_qnty / {capacity} * {dist}), 0)
                                                                                                         ELSE 0
                                                                                                         END
                                                                                                         +
                                                                                                         CASE WHEN {dist} > 2
                                                                                                         THEN IFNULL(sum(used_qnty / {capacity} * 2), 0)
                                                                                                         ELSE 0
                                                                                                         END) AS unpaved_fd_emissions,
                                      {k_b} * {sLS} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * (CASE WHEN {dist} <= 2
                                                                                        THEN IFNULL(SUM(used_qnty / {capacity} * 0), 0)
                                                                                        ELSE 0
                                                                                        END
                                                                                        +
                                                                                        CASE WHEN ({dist} > 2 AND {dist} <= 50)
                                                                                        THEN IFNULL(SUM(used_qnty / {capacity} * ({dist} - 2)), 0)
                                                                                        ELSE 0
                                                                                        END
                                                                                        +
                                                                                        CASE WHEN {dist} > 50
                                                                                        THEN IFNULL(SUM(used_qnty / {capacity} * (50)), 0)
                                                                                        ELSE 0
                                                                                        END) AS sec_paved_fd_emissions,
                                      {k_b} * {sLP} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * (CASE WHEN {dist}   <= 50
                                                                                        THEN IFNULL(SUM(used_qnty / {capacity} * 0), 0)
                                                                                        ELSE 0
                                                                                        END
                                                                                        +
                                                                                        CASE WHEN {dist} > 50
                                                                                        THEN IFNULL(SUM(used_qnty / {capacity} * ({dist} - 50)), 0)
                                                                                        ELSE 0
                                                                                        END) AS pri_paved_fd_emissions
                         FROM {production_schema}.{transport_table} td
                         LEFT JOIN {constants_schema}.state_road_data sd ON LEFT(td.sply_fips, 2) = sd.st_fips
                         WHERE feed_id = '{transport_feed_id}'
                         GROUP BY td.sply_fips
                         ;""".format(**self.kvals)

            self.db.input(query_fd)

            # # fugitive dust emissions from secondary and primary paved roads
            # query_sp = """UPDATE {scenario_name}.fugitive_dust
            #               SET    sec_paved_fd_emissions = (SELECT {k_b} * {sLS} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * IFNULL(SUM(used_qnty / {capacity} * 0), 0)
            #                                                FROM   {production_schema}.{transport_table}
            #                                                WHERE  sply_fips = {fips}
            #                                                  AND  feed_id   = '{transport_feed_id}'
            #                                                  AND  {dist}   <= 2
            #                                               ) +
            #                                               (SELECT {k_b} * {sLS} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * IFNULL(SUM(used_qnty / {capacity} * ({dist} - 2)), 0)
            #                                                FROM   {production_schema}.{transport_table}
            #                                                WHERE  sply_fips = {fips}
            #                                                  AND feed_id    = '{transport_feed_id}'
            #                                                  AND {dist}     > 2
            #                                                  AND {dist}    <= 50
            #                                               ) +
            #                                               (SELECT {k_b} * {sLS} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * IFNULL(SUM(used_qnty / {capacity} * (50)), 0)
            #                                                FROM   {production_schema}.{transport_table}
            #                                                WHERE  sply_fips = {fips}
            #                                                  AND feed_id    = '{transport_feed_id}'
            #                                                  AND {dist}     > 50
            #                                               ),
            #                      pri_paved_fd_emissions = (SELECT {k_b} * {sLP} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * IFNULL(SUM(used_qnty / {capacity} * 0), 0)
            #                                                FROM {production_schema}.{transport_table}
            #                                                WHERE sply_fips = {fips}
            #                                                  AND feed_id   = '{transport_feed_id}'
            #                                                  AND {dist}   <= 50
            #                                               ) +
            #                                               (SELECT {k_b} * {sLP} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * IFNULL(SUM(used_qnty / {capacity} * ({dist} - 50)), 0)
            #                                                FROM   {production_schema}.{transport_table}
            #                                                WHERE  sply_fips = {fips}
            #                                                  AND  feed_id   = '{transport_feed_id}'
            #                                                  AND  {dist}    > 50
            #                                               )
            #               WHERE  fips           = '{fips}'
            #                 AND  feedstock      = '{feed}'
            #                 AND  yearID         = '{year}'
            #                 AND  pollutantID    = '{pollutant_name}'
            #                 AND  logistics_type = '{logistics_type}'
            #                 AND  yield_type     = '{yield_type}'
            #               ;""".format(**self.kvals)
            #
            # self.db.input(query_sp)

            query_sum = """UPDATE {scenario_name}.fugitive_dust
                           SET    total_fd_emissions = sec_paved_fd_emissions + unpaved_fd_emissions + pri_paved_fd_emissions
                           WHERE  feedstock      = '{feed}'
                             AND  yearID         = '{year}'
                             AND  pollutantID    = '{pollutant_name}'
                             AND  logistics_type = '{logistics_type}'
                             AND  yield_type     = '{yield_type}'
                           ;""".format(**self.kvals)

            self.db.input(query_sum)

    def calculate_transport_emissions(self):
        """
        Calculate fugitive dust and combustion emissions generated by off-farm transportation
        Update transportation table with these values
        """
        # compute combustion and fugitive dust emissions from feedstock transport if transport data exists for feedstock type
        if self.kvals['transport_feed_id'] != 'None':
            self.process_moves_data()  # calculate total combustion emissions using MOVES emission rates
            self.transport_fugitive_dust()  # calculate total fugitive dust emissions from off-farm transport using EPA equations
