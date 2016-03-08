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

    def __init__(self, feed, cont, fips, vmt, pop, trips):
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
        # set other values in kvals dictionary
        self.kvals['fips'] = fips  # fips
        self.kvals['feed'] = feed  # feedstock name
        self.kvals['db_in'] = "fips_" + fips + "_" + feed + "_in"  # input database for MOVES run
        self.kvals['db_out'] = "fips_" + fips + "_" + feed + "_out"  # output database for MOVES run
        self.kvals['year'] = config['year_dict'][self.feed]  # year of scenario run
        self.kvals['scenarioID'] = '{fips}_{feed}'.format(**self.kvals)  # MOVES scenario ID
        self.kvals['vmt'] = vmt  # vehicle miles travelled
        self.kvals['pop'] = pop  # population of vehicles (#)
        self.kvals['trips'] = trips  # number of combination short-haul trips

        # dictionary of pollutant names and IDs
        self.pollutant_dict = {"NH3": "30",
                               "CO": "2",
                               "NOX": "3",
                               "PM10": "100",
                               "PM25": "110",
                               "SO2": "31",
                               "VOC": "87"}

        # open SQL connection and create cursor
        self.connection = pymysql.connect(host=self.kvals['MOVES_db_host'],
                                          user=self.kvals['MOVES_db_user'],
                                          password=self.kvals['MOVES_db_pass'],
                                          db=self.kvals['MOVES_database'])
        self.cursor = self.connection.cursor()

    def process_moves_data(self):
        """
        Post-process MOVES outputs to compute total combustion emissions from off-farm transport
        Update transportation table with these values

        Call function to compute total running emissions per trip
        Call function to compute total start emissions per trip
        Call function to compute total resting evaporative emissions per trip (currently zero)
        """
        logger.info('Post-processing MOVES output for %s' % self.feed)

        self.calc_run_emission()
        self.calc_start_hotel_emissions()
        self.calc_rest_evap_emissions()

        query = """ UPDATE output_{scenario_name}.transportation
                    SET total_emissions_per_trip= run_emissions + start_hotel_emissions + rest_evap_emissions,
                        number_trips='{trips}',
                        total_emissions = (run_emissions + start_hotel_emissions + rest_evap_emissions)*{trips};""".format(**self.kvals)
        self.cursor.execute(query)

    def calc_run_emission(self):
        """
        Calculate total running emissions per trip (by pollutant)
        Equal to sum(ratePerDistance * vmtfrac_in_speedbin[i] * vmt) for all speed bins, pollutant processes, day types, hours, and road types
        """

        for key in self.pollutant_dict:
            logger.info('Calculating running emissions for %s' % (key, ))

            # set pollutant name and ID
            self.kvals['pollutant_name'] = key
            self.kvals['pollutantID'] = self.pollutant_dict[key]

            query = """ INSERT INTO output_{scenario_name}.transportation (pollutantID, MOVESScenarioID, yearID, run_emissions)
                        VALUES('{pollutant_name}',
                               '{scenarioID}',
                               '{year}',
                               (SELECT sum(table1.ratePerDistance*table2.avgSpeedFraction*{vmt}) AS run_emissions
                                FROM {db_out}.rateperdistance table1
                                LEFT JOIN output_{scenario_name}.averagespeed table2
                                ON table1.hourID = table2.hourID AND
                                table1.dayID = table2.dayID AND
                                table1.roadTypeID = table2.roadTypeID AND
                                table1.avgSpeedBinID = table2.avgSpeedBinID
                                WHERE table1.pollutantID = {pollutantID}
                                GROUP BY table1.MOVESScenarioID, table1.yearID, table1.pollutantID));""".format(**self.kvals)
            self.cursor.execute(query)

    def calc_start_hotel_emissions(self):
        """
        Calculate total start and hoteling emissions per trip (by pollutant)
        Equal to sum(output.ratePerVehicle * pop) for all pollutant processes, days, hours, and road types
        """

        for key in self.pollutant_dict:
            logger.info('Calculating start emissions for %s' % (key, ))

            # set pollutant name and ID
            self.kvals['pollutant_name'] = key
            self.kvals['pollutantID'] = self.pollutant_dict[key]

            query = """ UPDATE output_{scenario_name}.transportation
                        SET pollutantID='{pollutant_name}',
                            MOVESScenarioID='{scenarioID}',
                            yearID='{year}',
                            start_hotel_emissions=(SELECT sum(table1.ratePerVehicle*{pop}) AS start_hotel_emissions
                                                   FROM {db_out}.ratepervehicle table1
                                                   WHERE table1.pollutantID = {pollutantID}
                                                   GROUP BY table1.MOVESScenarioID, table1.yearID, table1.pollutantID)
                        WHERE pollutantID='{pollutant_name}';""".format(**self.kvals)

            self.cursor.execute(query)

    def calc_rest_evap_emissions(self):
        """
        Calculate total resting evaporative fuel vapor venting rates
        Currently set to zero because only using 12 hr time span and resting evaporative rates require 24 hr selection
        """
        logger.warning('Resting evaporative fuel vapor venting rates are currently zero')
        # @TODO: if we decide to include evaporative fuel vapor venting emissions, add code for processing MOVES outputs
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

        self.process_moves_data()
        self.transport_fugitive_dust()

        self.cursor.close()
