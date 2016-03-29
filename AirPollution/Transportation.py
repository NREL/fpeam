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
from src.AirPollution.utils import config, logger
import pymysql


class Transportation(SaveDataHelper.SaveDataHelper):
    """
    Computes the emissions associated with off-farm transportation
    """

    def __init__(self, feed, cont, fips, vmt, pop, logistics_type, silt, yield_type):
        """

        :param feed: feedstock to process
        :param cont: Container object
        :param fips: FIPS code
        :return:
        """
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.feed = feed
        self.fips = fips
        self.document_file = "Logistics"  # filename for saving queries to text file for debugging

        self.kvals = dict()
        # get MOVES database info and scenario name
        self.kvals['moves_database'] = config.get('moves_database')  # MOVES database name
        self.kvals['moves_db_user'] = config.get('moves_db_user')  # username for MOVES database
        self.kvals['moves_db_pass'] = config.get('moves_db_pass')  # password for MOVES database
        self.kvals['moves_db_host'] = config.get('moves_db_host')  # host for MOVES database
        self.kvals['scenario_name'] = config.get('title')  # scenario name
        # get production and constants schemas
        self.kvals['production_schema'] = config.get('production_schema')
        self.kvals['constants_schema'] = config.get('constants_schema')
        # set other values in kvals dictionary
        self.kvals['fips'] = fips  # fips
        self.kvals['feed'] = feed  # feedstock name

        self.kvals['year'] = config['year_dict'][self.feed]  # year of scenario run
        self.kvals['scenarioID'] = '{fips}_{feed}'.format(**self.kvals)  # MOVES scenario ID
        self.kvals['vmt'] = vmt  # vehicle miles travelled
        self.kvals['pop'] = pop  # population of vehicles (#)
        self.kvals['g_per_mt'] = 1e6  # number of grams in one metric ton

        self.kvals['s'] = silt  # unpaved road surface material silt content that corresponds to fips code
        self.kvals['logistics_type'] = logistics_type

        feed_type_dict = config.get('feed_type_dict')
        self.kvals['transport_table'] = config.get('transport_table_dict')[feed_type_dict[feed]][yield_type][logistics_type]

        # get toggle for running moves by crop
        moves_by_crop = config.get('moves_by_crop')

        # set moves database names
        self.kvals['db_out'] = "{moves_output_db}".format(moves_output_db=config.get('moves_output_db'))  # output database for MOVES run (output database same for all crops)

        # set input database and scenario id depending on moves_by_crop
        if moves_by_crop is True:
            self.kvals['db_in'] = "fips_{fips}_{feed}_in".format(fips=fips, feed=feed)  # input database for MOVES run
            self.kvals['moves_scen_id'] = "{fips}_{crop}_{year}_{month}_{day}".format(fips=fips, crop=feed, day=config.get('moves_timespan')['d'][0], month=config.get('moves_timespan')['mo'][0], year=self.kvals['year'])
        else:
            self.kvals['db_in'] = "fips_{fips}_{feed}_in".format(fips=fips, feed='all_crops')  # input database for MOVES run
            self.kvals['moves_scen_id'] = "{fips}_all_crops_{year}_{month}_{day}".format(fips=fips, crop=feed, day=config.get('moves_timespan')['d'][0], month=config.get('moves_timespan')['mo'][0], year=self.kvals['year'])

        # dictionary of column names for transportation data
        self.transport_column = config.get('transport_column')

        # dictionary of pollutant names and IDs
        self.pollutant_dict = config.get('pollutant_dict')

        # dictionary of feedstock ids for transportation data
        self.feed_id_dict = config.get('feed_id_dict')

        # dictionary of truck capacities
        self.truck_capacity = config.get('truck_capacity')

        # kvals value for truck capacity
        self.kvals['capacity'] = self.truck_capacity[self.feed][self.kvals['logistics_type']]

        # open SQL connection and create cursor
        # @TODO: change to use Database.py once all data in MySQL
        self.connection = pymysql.connect(host=self.kvals['moves_db_host'],
                                          user=self.kvals['moves_db_user'],
                                          password=self.kvals['moves_db_pass'],
                                          db=self.kvals['moves_database'])
        self.cursor = self.connection.cursor()

        # set feedstock ID
        self.kvals['feed_id'] = self.feed_id_dict[self.feed]

    def process_moves_data(self):
        """
        Post-process MOVES outputs to compute total combustion emissions from off-farm transport

        Call function to compute total running emissions per trip
        Call function to compute total start emissions per trip
        Call function to compute total resting evaporative emissions per trip (currently zero)

        Update transportation table with total emissions
        """
        logger.info('Post-processing MOVES output for fips={fips}, feed={feed}, logistics={logistics_type}'.format(**self.kvals))

        self.calc_run_emission()
        self.calc_start_hotel_emissions()
        self.calc_rest_evap_emissions()

        # @TODO: replace {constants_schema}.transport with correct table once data imported into MySQL
        # @TODO: column names appear to have changed for latest logistics data - double check that "used_qnty", "sply_fips", and "feed_id" are correctly named
        query = """ UPDATE output_{scenario_name}.transportation
                    SET total_emissions_per_trip = run_emissions + start_hotel_emissions + rest_evap_emissions,
                        number_trips = (SELECT IFNULL(sum(used_qnty / {capacity}), 0)
                                        FROM {production_schema}.{transport_table}
                                        WHERE sply_fips = '{fips}' AND feed_id = '{feed_id}'),
                        total_emissions = (run_emissions + start_hotel_emissions + rest_evap_emissions) * (SELECT IFNULL(sum(used_qnty / {capacity}), 0)
                                                                                                           FROM {production_schema}.{transport_table}
                                                                                                           WHERE sply_fips = '{fips}' AND feed_id = '{feed_id}')
                    WHERE feedstock = '{feed}' AND fips = '{fips}' AND logistics_type = '{logistics_type}';""".format(**self.kvals)
        self.cursor.execute(query)

    def calc_run_emission(self):
        """
        Calculate total running emissions per trip (by pollutant)
        Equal to sum(ratePerDistance * vmtfrac_in_speedbin[i] * vmt) for all speed bins, pollutant processes, day types, hours, and road types
        Insert values into transportation table
        """

        for key in self.pollutant_dict:
            logger.info('Calculating running emissions for %s' % (key, ))

            # set pollutant name and ID
            self.kvals['pollutant_name'] = key
            self.kvals['pollutantID'] = self.pollutant_dict[key]

            query = """ INSERT INTO output_{scenario_name}.transportation (pollutantID, fips, feedstock, yearID, logistics_type, run_emissions)
                        VALUES('{pollutant_name}',
                               '{fips}',
                               '{feed}',
                               '{year}',
                               '{logistics_type}',
                               (SELECT sum(table1.ratePerDistance * table2.avgSpeedFraction * {vmt} / {g_per_mt}) AS run_emissions
                                FROM {db_out}.rateperdistance table1
                                LEFT JOIN output_{scenario_name}.averageSpeed table2
                                ON table1.hourID = table2.hourID AND
                                table1.dayID = table2.dayID AND
                                table1.roadTypeID = table2.roadTypeID AND
                                table1.avgSpeedBinID = table2.avgSpeedBinID
                                WHERE table1.pollutantID = {pollutantID} AND table1.MOVESScenarioID = '{moves_scen_id}'
                                GROUP BY table1.yearID, table1.pollutantID));""".format(**self.kvals)
            self.cursor.execute(query)

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

            query = """ UPDATE output_{scenario_name}.transportation
                        SET start_hotel_emissions = (SELECT sum(table1.ratePerVehicle * {pop} / {g_per_mt}) AS start_hotel_emissions
                                                     FROM {db_out}.ratepervehicle table1
                                                     WHERE table1.pollutantID = {pollutantID} AND table1.MOVESScenarioID = '{moves_scen_id}'
                                                     GROUP BY table1.yearID, table1.pollutantID)
                        WHERE pollutantID = '{pollutant_name}' AND fips = '{fips}' AND feedstock = '{feed}' AND yearID = '{year}' AND logistics_type = '{logistics_type}';""".format(**self.kvals)
            self.cursor.execute(query)

    def calc_rest_evap_emissions(self):
        """
        Calculate total resting evaporative fuel vapor venting rates
        Currently zero because only using 12 hr time span and resting evaporative rates require 24 hr selection
        Also, MOVES assumes that diesel fuel has zero evaporative venting emissions
        """
        logger.warning('Resting evaporative fuel vapor venting rates are zero for diesel fuel')
        logger.warning('Additional code required to processing fuel vapor evap emissions if fuel type is not diesel')
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
        logger.debug('Calculating fugitive dust emissions for fips={fips}, feed={feed}'.format(**self.kvals))

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

            self.kvals['feed_id'] = self.feed_id_dict[self.feed]

            self.kvals['dist'] = self.transport_column[self.kvals['logistics_type']]['dist']

            # fugitive dust emissions from unpaved roads
            # @TODO: replace {constants_schema}.{transport_table} with correct table once data imported into MySQL - check transport_table dict in config
            # @TODO: column names appear to have changed for latest logistics data - check transport_column dict in config
            # @TODO: also check values for feed_id (e.g., corn stover was CORNSV but now it looks like it might be "Corn stover") - check feed_id_dict in config
            query_u = """INSERT INTO output_{scenario_name}.fugitive_dust (fips, feedstock, yearID, pollutantID, logistics_type, unpaved_fd_emissions)
                       VALUES ('{fips}',
                               '{feed}',
                               '{year}',
                               '{pollutant_name}',
                               '{logistics_type}',
                               (SELECT {c} * {k_a} * ({s} / 12) ^ {a} * ({W} / 3) ^ {b} * IFNULL(sum(used_qnty / {capacity} * {dist}), 0)
                                FROM {production_schema}.{transport_table}
                                WHERE sply_fips = '{fips}' AND feed_id = '{feed_id}' AND {dist} <= 2) +
                               (SELECT {c} * 2 * {k_a} * ({s} / 12) ^ {a} * ({W} / 3) ^ {b} * IFNULL(sum(used_qnty / {capacity} * 2), 0)
                                FROM {production_schema}.{transport_table}
                                WHERE sply_fips = '{fips}' AND feed_id = '{feed_id}' AND {dist} > 2));""".format(**self.kvals)

            # fugitive dust emissions from secondary paved roads (conventional system)
            query_sp = None
            if self.kvals['logistics_type'] == 'C':
                # @TODO: replace {constants_schema}.{transport_table} with correct table once data imported into MySQL - check transport_table dict in config
                # @TODO: column names appear to have changed for latest logistics data - check transport_column dict in config
                # @TODO: also check values for feed_id (e.g., corn stover was CORNSV but now it looks like it might be "Corn stover") - check feed_id_dict in config
                query_sp = """UPDATE output_{scenario_name}.fugitive_dust
                           SET sec_paved_fd_emissions = (SELECT {k_b} * {sLS} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * IFNULL(sum(used_qnty / {capacity} * 0), 0)
                                                         FROM {production_schema}.{transport_table}
                                                         WHERE sply_fips = '{fips}' AND feed_id = '{feed_id}' AND {dist} <= 2) +
                                                        (SELECT {k_b} * {sLS} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * IFNULL(sum(used_qnty / {capacity} * ({dist} - 2)), 0)
                                                         FROM {production_schema}.{transport_table}
                                                         WHERE sply_fips = '{fips}' AND feed_id = '{feed_id}' AND {dist} > 2)
                           WHERE fips = '{fips}' AND feedstock = '{feed}' AND yearID = '{year}' AND pollutantID = '{pollutant_name}' AND logistics_type = '{logistics_type}';
                           """.format(**self.kvals)

            # fugitive dust emissions from secondary paved roads (advanced system)
            if self.kvals['logistics_type'] == 'A':
                self.kvals['dist_2'] = self.transport_column[self.kvals['logistics_type']]['dist_2']

                # @TODO: replace {constants_schema}.{transport_table} with correct table once data imported into MySQL - check transport_table dict in config
                # @TODO: column names appear to have changed for latest logistics data - check transport_column dict in config
                # @TODO: also check values for feed_id (e.g., corn stover was CORNSV but now it looks like it might be "Corn stover") - check feed_id_dict in config
                query_sp = """UPDATE output_{scenario_name}.fugitive_dust
                       SET sec_paved_fd_emissions = (SELECT {k_b} * {sLS} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * IFNULL(sum(used_qnty / {capacity} * {dist_2}), 0)
                                                     FROM {production_schema}.{transport_table}
                                                     WHERE sply_fips = '{fips}' AND feed_id = '{feed_id}' AND {dist} <= 2) +
                                                    (SELECT {k_b} * {sLS} ^ 0.91 * {W} ^ 1.02 / {g_per_mt} * IFNULL(sum(used_qnty / {capacity} * (({dist} - 2) + {dist_2})), 0)
                                                     FROM {production_schema}.{transport_table}
                                                     WHERE sply_fips = '{fips}' AND feed_id = '{feed_id}' AND {dist} > 2)
                       WHERE fips = '{fips}' AND feedstock = '{feed}' AND yearID = '{year}' AND pollutantID = '{pollutant_name}' AND logistics_type = '{logistics_type}';
                       """.format(**self.kvals)

            self.cursor.execute(query_u)
            self.cursor.execute(query_sp)

            query_sum = """UPDATE output_{scenario_name}.fugitive_dust
                           SET total_fd_emissions = sec_paved_fd_emissions + unpaved_fd_emissions
                           WHERE fips = '{fips}' AND feedstock = '{feed}' AND yearID = '{year}' AND pollutantID = '{pollutant_name}' AND logistics_type = '{logistics_type}';
                           """.format(**self.kvals)
            self.cursor.execute(query_sum)

    def calculate_transport_emissions(self):
        """
        Calculate fugitive dust and combustion emissions generated by off-farm transportation
        Update transportation table with these values
        """
        # compute combustion and fugitive dust emissions from feedstock transport if transport data exists for feedstock type
        if self.kvals['feed_id'] != 'None':
            self.process_moves_data()
            self.transport_fugitive_dust()

        self.cursor.close()
