# -*- coding: utf-8 -*-
"""
Created on Thur Mar 3 9:24:46 2016

Populates tables for transportation emissions associated with off-farm transport

Inputs include:
    list of feedstock types (feedstock_list)
    container (cont)

@author: aeberle
"""

import SaveDataHelper
from src.AirPollution.utils import config, logger
import pymysql


class Transportation(SaveDataHelper.SaveDataHelper):
    """
    Computes the emissions associated with off-farm transportation
    """

    def __init__(self, feed, cont, fips, vmt):
        """

        :param feed: feedstock to process
        :param cont: Container object
        :param fips: FIPS code
        :return:
        """
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.feed = feed
        self.document_file = "Logistics"  # filename for saving queries to text file for debugging

        self.kvals = dict()
        # get MOVES database info and scenario name
        self.kvals['MOVES_database'] = config.get('MOVES_database')  # MOVES database name
        self.kvals['MOVES_db_user'] = config.get('MOVES_db_user')  # username for MOVES database
        self.kvals['MOVES_db_pass'] = config.get('MOVES_db_pass')  # password for MOVES database
        self.kvals['MOVES_db_host'] = config.get('MOVES_db_host')  # host for MOVES database
        self.kvals['scenario_name'] = config.get('title')  # scenario name

        # set vmt
        self.kvals['vmt'] = vmt

        self.column_dict = dict()
        # create dictionary for column names for production data
        self.column_dict['CG'] = 'total_prod'
        self.column_dict['CS'] = 'prod'
        self.column_dict['WS'] = 'prod'
        self.column_dict['SG'] = 'prod'
        self.column_dict['FR'] = 'fed_minus_55'

        # create strings for input and output databases
        self.db_in = "fips_" + fips + "_" + feed + "_in"  # input database for MOVES runs
        self.db_out = "fips_" + fips + "_" + feed + "_out"  # output database for MOVES runs

        # set fips
        self.kvals['fips'] = fips
        self.kvals['feed'] = feed

    def process_moves_data(self, cursor):
        """
        Post-process MOVES outputs to compute total combustion emissions from off-farm transport
        Update transportation table with these values

        Call function to compute total running emissions per trip
        Call function to compute total start emissions per trip
        Call function to compute total resting evaporative emissions per trip (currently zero)

        :param cursor: cursor for database query
        """
        logger.info('Post-processing MOVES output for %s' % self.feed)

        self.calc_run_emission(cursor)
        self.calc_start_emissions()
        self.calc_rest_evap_emissions()

    def calc_run_emission(self, cursor):
        """
        Total running emissions per trip (by pollutant) = sum over i = 1 to 16 for (SELECT sum(ratePerDistance * vmtfrac_in_speedbin[i] * vmt)
                                                                                    FROM output.rateperdistance
                                                                                    WHERE pollutantID = value AND (processID = 2 OR processID = 16) AND avgSpeedBinID = i)
        :param cursor: cursor for database query
        """
        # @TODO: currently assumes tables are already created; need to add code to create tables


        self.kvals['db_in'] = self.db_in
        self.kvals['db_out'] = self.db_out
        self.kvals['year'] = config['year_dict'][self.feed]
        self.kvals['scenarioID'] = '{fips}_{feed}'.format(**self.kvals)

        polkey = {"NH3": "30",
                  "CO": "2",
                  "NOX": "3",
                  "PM10": "100",
                  "PM25": "110",
                  "SO2": "31",
                  "VOC": "87"}
        for key in polkey:
            # set pollutant name and ID
            self.kvals['pollutant_name'] = key
            self.kvals['pollutantID'] = polkey[key]
            logger.info('Calculating running emissions for %s' % (key, ))
            query = """INSERT INTO output_{scenario_name}.transportation (pollutantID, MOVESScenarioID, yearID, total_emissions)
                    VALUES('{pollutant_name}', '{scenarioID}', '{year}', (SELECT sum(table1.ratePerDistance*table2.avgSpeedFraction*{vmt}) AS total_emissions
                                                                            FROM {db_out}.rateperdistance table1
                                                                            LEFT JOIN output_{scenario_name}.averagespeed table2
                                                                            ON table1.hourID = table2.hourID AND
                                                                            table1.dayID = table2.dayID AND
                                                                            table1.roadTypeID = table2.roadTypeID AND
                                                                            table1.avgSpeedBinID = table2.avgSpeedBinID
                                                                            WHERE table1.pollutantID = {pollutantID}
                                                                            GROUP BY table1.MOVESScenarioID, table1.yearID, table1.pollutantID));""".format(**self.kvals)
            print query
            cursor.execute(query)

    def calc_start_emissions(self):
        """
        Total start emissions per trip (by pollutant) = SELECT sum(output.ratePerVehicle * pop)
                                                        FROM output.ratepervehicle
                                                        WHERE pollutantID = value AND (processID = 17 OR processID = 90 OR processID = 91)
        """
        logger.debug('Calculating start emissions')
        # @TODO: replace with code for processing MOVES outputs
        pass

    def calc_rest_evap_emissions(self):
        """
        Total resting evaporative fuel vapor venting rates are set to zero because only using 12 hr time span and resting evaporative rates require 24 hr selection
        :return:
        """
        logger.debug('Calculating resting evaporative fuel vapor venting emissions')
        logger.warning('Resting evaporative fuel vapor venting rates are currently zero')
        # @TODO: replace with code for processing MOVES outputs
        pass

    def transport_fugitive_dust(self):
        """
        Compute fugitive dust emissions generated by off-farm transportation
        Update transportation table with these values
        """
        # @TODO: replace with code for calculating fugitive dust
        logger.debug('Calculating fugitive dust emissions')
        logger.warning('Fugitive dust emissions are currently zero')
        pass

    def calculate_transport_emissions(self):
        """
        Calculate fugitive dust and combustion emissions generated by off-farm transportation
        Update transportation table with these values
        """
        connection = pymysql.connect(host=self.kvals['MOVES_db_host'], user=self.kvals['MOVES_db_user'], password=self.kvals['MOVES_db_pass'], db=self.kvals['MOVES_database'])
        cursor = connection.cursor()

        self.process_moves_data(cursor)
        self.transport_fugitive_dust()

        cursor.close()
