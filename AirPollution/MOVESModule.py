# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 11:00:20 2016

Generates XML files for importing data and running MOVES
Also creates batch files for executing MOVES imports and runs 

Inputs include:
    crop type
    list of FIPS codes
    year of scenario
    path to MOVES (where batch files are saved for execution)
    path to XML import files
    path to XML runspec files
    path to county data input files 

@author: aeberle
"""

import csv
import os
import subprocess

import GenerateMOVESImport as GenMOVESIm
import GenerateMOVESRunspec as GenMOVESRun
import MOVESBatch as MOVESBatch
from utils import config, logger


class MOVESModule:
    """
    Generate XML files for import and runspec files and creates batch files for importing and running MOVES
    """

    def __init__(self, crop, fips, yr_list, path_moves, save_path_importfiles, save_path_runspecfiles, save_path_countyinputs, save_path_nationalinputs, db):
        self.crop = crop  # crop name
        self.fips = fips  # list of FIPS codes
        self.yr_list = yr_list  # scenario year list
        self.yr = yr_list[crop]  # scenario year for specific feedstock
        self.path_moves = path_moves  # path for MOVES program
        self.save_path_importfiles = save_path_importfiles  # path for MOVES import files
        self.save_path_runspecfiles = save_path_runspecfiles  # path for MOVES run spec files
        self.save_path_countyinputs = save_path_countyinputs  # path for MOVES county data input files
        self.save_path_nationalinputs = save_path_nationalinputs  # path for national input data files for MOVES

        # get information from config file 
        self.model_run_title = config.get('title')  # scenario title
        self.moves_database = config.get('moves_database')  # MOVES database name
        self.moves_db_user = config.get('moves_db_user')  # username for MOVES database
        self.moves_db_pass = config.get('moves_db_pass')  # password for MOVES database
        self.moves_db_host = config.get('moves_db_host')  # host for MOVES database
        self.moves_timespan = config.get('moves_timespan')  # time span for MOVES runs
        self.constants_schema = config.get('constants_schema')
        self.age_distribution = config.get('age_distribution')  # age distribution dictionary for MOVES runs (varies by scenario year)
        self.vmt_fraction = config.get('vmt_fraction')  # fraction of VMT by road type
        self.fuelfraction = config.get('fuel_fraction')  # fuel fraction
        self.db = db  # database object

    def _get_and_write_data_file_lines(self, query, fname):
        """
        Helper function to query and write data

        :param query: SQL statement
        :param fname: file path
        :return:
        """

        # connect to MOVES database
        with self.db.connect() as cursor:

            # execute query
            cursor.execute(query)

            # open and write lines
            with open(fname, 'wb') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow([i[0] for i in cursor.description])  # write headers
                csv_writer.writerows(cursor)

            # close cursor
            cursor.close()

    def create_county_data(self, vmt_short_haul, pop_short_haul):
        """
        Create county-level data for MOVES, including:
            vehicle miles travelled
            source type population
            fuel supply type
            fuel formulation
            fuel usage fraction
            meteorology

        :param vmt_short_haul = annual vehicle miles traveled by combination short-haul trucks
        :param pop_short_haul = population of combination short-haul trucks
        :return: 
        """

        logger.debug('Creating county-level data files for MOVES')

        # set fips
        fips = self.fips

        # define zoneID and countyID for querying MOVES database
        zone_id = str(int(fips)) + '0'  # @TODO: is zoneID always FIPS + 0 or should this be a padded to some length?
        county_id = str(int(fips))
        kvals = dict()
        kvals['fips'] = fips
        kvals['crop'] = self.crop
        kvals['year'] = self.yr
        kvals['moves_database'] = self.moves_database
        kvals['countyID'] = county_id
        kvals['zoneID'] = zone_id

        # county-level input files for MOVES that vary by FIPS, year, and crop
        # (these inputs are calculated by FPEAM based on production data)
        vmtname = os.path.join(self.save_path_countyinputs, '{fips}_vehiclemiletraveled_{year}_{crop}.csv'.format(**kvals))
        sourcetypename = os.path.join(self.save_path_countyinputs, '{fips}_sourcetype_{year}_{crop}.csv'.format(**kvals))

        # annual vehicle miles traveled by vehicle type
        with open(vmtname, 'wb') as csvfile:
            vmtwriter = csv.writer(csvfile, dialect='excel')
            vmtwriter.writerow(['HPMSVtypeID', 'yearID', 'HPMSBaseYearVMT'])
            vmtwriter.writerow(['60', self.yr, vmt_short_haul])  # combination short-haul truck

        # source type population (number of vehicles by vehicle type)
        with open(sourcetypename, 'wb') as csvfile:
            popwriter = csv.writer(csvfile, dialect='excel')
            popwriter.writerow(['yearID', 'sourceTypeID', 'sourceTypePopulation'])
            popwriter.writerow([self.yr, '61', pop_short_haul])  # combination short-haul truck

        # county-level input files for MOVES that vary by FIPS and year
        fuelsupplyname = os.path.join(self.save_path_countyinputs, '{fips}_fuelsupply_{year}.csv'.format(**kvals))
        fuelformname = os.path.join(self.save_path_countyinputs, '{fips}_fuelformulation_{year}.csv'.format(**kvals))
        fuelusagename = os.path.join(self.save_path_countyinputs, '{fips}_fuelusagefraction_{year}.csv'.format(**kvals))

        # export county-level fuel supply data
        sql = """SELECT * FROM {moves_database}.fuelsupply
                            WHERE {moves_database}.fuelsupply.fuelRegionID =
                            (SELECT DISTINCT regionID FROM {moves_database}.regioncounty WHERE countyID = '{countyID}' AND fuelYearID = '{year}')
                            AND {moves_database}.fuelsupply.fuelYearID = '{year}'""".format(**kvals)
        self._get_and_write_data_file_lines(sql, fuelsupplyname)

        # export county-level fuel formulation data
        sql = """SELECT * FROM {moves_database}.fuelformulation
                            WHERE {moves_database}.fuelformulation.fuelSubtypeID = '21'
                            OR {moves_database}.fuelformulation.fuelSubtypeID = '20';""".format(**kvals)
        self._get_and_write_data_file_lines(sql, fuelformname)

        # export county-level fuel usage fraction data
        sql = """SELECT * FROM {moves_database}.fuelusagefraction
                            WHERE {moves_database}.fuelusagefraction.countyID = '{countyID}'
                            AND {moves_database}.fuelusagefraction.fuelYearID = '{year}'
                            AND {moves_database}.fuelusagefraction.fuelSupplyFuelTypeID = '2';""".format(**kvals)
        self._get_and_write_data_file_lines(sql, fuelusagename)

        # county-level input files for MOVES that vary by FIPS
        met_name = os.path.join(self.save_path_countyinputs, '%s_met.csv' % (fips, ))

        # export county-level meteorology data
        sql = """SELECT * FROM {moves_database}.zonemonthhour WHERE {moves_database}.zonemonthhour.zoneID = {zoneID}""".format(**kvals)
        self._get_and_write_data_file_lines(sql, met_name)

    def create_national_data(self):
        """
        Create national data for MOVES, including: 
            Alternate Vehicle Fuels & Technologies (avft)
            average speed distribution
            age distribution (currently only works for 2015, 2017, 2022, and 2040)
            day VMT fraction
            month VMT fraction
            hour VMT fraction
            road type fraction

        :return:
        """

        logger.debug('Creating national data files for MOVES')

        # initialize kvals for string formatting
        kvals = dict()
        kvals['year'] = self.yr
        kvals['moves_database'] = self.moves_database

        # export MOVES defaults for national inputs (i.e., hourVMTFraction, monthVMTFraction, dayVMTFraction, and avgspeeddistribution)
        tables = ['hourvmtfraction', 'monthvmtfraction', 'dayvmtfraction', 'avgspeeddistribution']
        for table in tables:
            kvals['table'] = table
            filename = os.path.join(self.save_path_nationalinputs, '%s.csv' % (kvals['table'], ))
            sql = """SELECT * FROM {moves_database}.{table} WHERE sourceTypeID = '61';""".format(**kvals)
            self._get_and_write_data_file_lines(query=sql, fname=filename)

        # create file for alternative vehicle fuels and technology (avft)
        sourcetype = '61'
        engtech = '1'
        avftname = os.path.join(self.save_path_nationalinputs, 'avft.csv')
        with open(avftname, "wb") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(['sourceTypeID', 'modelYearID', 'fuelTypeID', 'engTechID', 'fuelEngFraction'])  # write headers
            i = 0
            for modelyear in range(1960, 2051):
                for fueltype in range(1, 3):
                    csv_writer.writerow([sourcetype, modelyear, fueltype, engtech, self.fuelfraction[i]])
                    i += 1

        # create file for default age distribution (values in age_distribution dictionary were computed using MOVES Default Age Distribution Tool)
        for feed in self.yr_list:
            agedistname = os.path.join(self.save_path_nationalinputs, 'default-age-distribution-tool-moves%s.csv' % (self.yr_list[feed], ))
            with open(agedistname, 'wb') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(['sourceTypeID', 'yearID', 'ageID', 'ageFraction'])
                for bins in range(0, 31):
                    csv_writer.writerow(['61', self.yr_list[feed], bins, self.age_distribution[self.yr_list[feed]][bins]])

        # create file for road type fraction 
        roadtypename = os.path.join(self.save_path_nationalinputs, 'roadtype.csv')
        with open(roadtypename, 'wb') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(['sourceTypeID', 'roadTypeID', 'roadTypeVMTFraction'])
            for roadtype in range(2, 6):
                csv_writer.writerow(['61', roadtype, self.vmt_fraction[str(roadtype)]])

    def create_batch_files(self):
        """
        Create batch files for importing data using MOVES county data manager and running MOVES

        :return: {run_filename: <string>, im_filename: <string>}
        """

        logger.debug('Creating batch files for MOVES runs')

        run_filename = None
        im_filename = None

        # set fips
        fips = self.fips

        # check MOVES metadata table to see if MOVES was already run for this FIPS, yearID, monthID, and dayID
        # get data MOVES scenario ID from database if scenario ID matches this FIPS, yearID, monthID, and dayID
        query = """SELECT scen_id
                   FROM {constants_schema}.moves_metadata
                   WHERE scen_id = "{fips}_{crop}_{year}_{month}_{day}";""".format(constants_schema=self.constants_schema, fips=fips, crop=self.crop, day=self.moves_timespan['d'][0], month=self.moves_timespan['mo'][0], year=self.yr)
        scen_id_output = self.db.output(query)

        # set moves_output_exists default to false
        moves_output_exists = False
        if scen_id_output is not None:
            # if query for MOVES scenario ID returns a value, check to make sure matches this FIPS, yearID, monthID, and dayID and then set moves_output_exists to true
            if scen_id_output[0][0][0] == "{fips}_{crop}_{year}_{month}_{day}".format(fips=fips, crop=self.crop, day=self.moves_timespan['d'][0], month=self.moves_timespan['mo'][0], year=self.yr):  # scenario ID for MOVES runs
                moves_output_exists = True

        moves_output_exists = False

        # instantiate MOVESBatch if MOVES output does not already exist
        if moves_output_exists is False:
            batch_file = MOVESBatch.MOVESBatch(crop=self.crop, model_run_title=self.model_run_title, fips=fips, yr=self.yr, path_moves=self.path_moves,
                                               save_path_importfiles=self.save_path_importfiles, save_path_runspecfiles=self.save_path_runspecfiles)

            # create MOVES batch import file
            im_filename = batch_file.importfilename

            # create MOVES batch run file
            run_filename = batch_file.runfilename

        return {'run_filename': run_filename,
                'im_filename': im_filename,
                'moves_output_exists': moves_output_exists
                }

    def create_xml_import(self):
        """
        Create XML files for importing data using MOVES county data manager

        :return:
        """

        logger.debug('Creating XML files for importing MOVES data')

        # filepaths for national MOVES defaults 
        agefilename = os.path.join(self.save_path_nationalinputs, "default-age-distribution-tool-moves%s.csv" % (self.yr, ))
        speedfilename = os.path.join(self.save_path_nationalinputs, "avgspeeddistribution.csv")
        avftfilename = os.path.join(self.save_path_nationalinputs, "avft.csv")
        roadtypefilename = os.path.join(self.save_path_nationalinputs, "roadtype.csv")
        monthvmtfilename = os.path.join(self.save_path_nationalinputs, "monthvmtfraction.csv")
        dayvmtfilename = os.path.join(self.save_path_nationalinputs, "dayvmtfraction.csv")
        hourvmtfilename = os.path.join(self.save_path_nationalinputs, "hourvmtfraction.csv")

        # set fips
        fips = self.fips

        kvals = {'fips': fips,
                 'year': self.yr,
                 'crop': self.crop
                 }

        # filepaths for county-level input files
        metfilename = os.path.join(self.save_path_countyinputs, '{fips}_met.csv'.format(**kvals))
        fuelsupfilename = os.path.join(self.save_path_countyinputs, '{fips}_fuelsupply_{year}.csv'.format(**kvals))
        fuelformfilename = os.path.join(self.save_path_countyinputs, '{fips}_fuelformulation_{year}.csv'.format(**kvals))
        fuelusagefilename = os.path.join(self.save_path_countyinputs, '{fips}_fuelusagefraction_{year}.csv'.format(**kvals))
        sourcetypename = os.path.join(self.save_path_countyinputs, '{fips}_sourcetype_{year}_{crop}.csv'.format(**kvals))
        vmtname = os.path.join(self.save_path_countyinputs, '{fips}_vehiclemiletraveled_{year}_{crop}.csv'.format(**kvals))

        # create import filename using FIPS code, crop, and scenario year
        im_filename = os.path.join(self.save_path_importfiles, '{fips}_import_{year}_{crop}.mrs'.format(fips=fips, year=self.yr, crop=self.crop))

        # instantiate GenerateMOVESImport class
        xmlimport = GenMOVESIm.GenerateMOVESImport(crop=self.crop, fips=fips, yr=self.yr, moves_timespan=self.moves_timespan, agefilename=agefilename,
                                                   speedfilename=speedfilename, fuelsupfilename=fuelsupfilename, fuelformfilename=fuelformfilename,
                                                   fuelusagefilename=fuelusagefilename, avftfilename=avftfilename, metfilename=metfilename,
                                                   roadtypefilename=roadtypefilename, sourcetypefilename=sourcetypename, vmtfilename=vmtname,
                                                   monthvmtfilename=monthvmtfilename, dayvmtfilename=dayvmtfilename, hourvmtfilename=hourvmtfilename, server=self.moves_db_host)

        # execute function for creating XML import file
        xmlimport.create_import_file(im_filename)

    def create_xml_runspec(self):
        """
        Create XML file for running MOVES

        :return:
        """

        logger.debug('Creating XML files for running MOVES')

        # set fips
        fips = self.fips

        # create filename for runspec file using FIPS code, crop, and scenario year
        run_filename = os.path.join(self.save_path_runspecfiles, '{fips}_runspec_{year}_{crop}.mrs'.format(fips=fips, year=self.yr, crop=self.crop))

        # instantiate GenerateMOVESRunspec class
        xmlrunspec = GenMOVESRun.GenerateMOVESRunSpec(crop=self.crop, fips=fips, yr=self.yr, moves_timespan=self.moves_timespan, server=self.moves_db_host)

        # execute function for creating XML file
        xmlrunspec.create_runspec_files(run_filename)

    def import_data(self, filename):
        """
        Import MOVES data into MySQL database

        :param filename: name of batch import file
        :return:
        """

        logger.debug('Importing MOVES files')

        # execute batch file and log output
        command = 'cd {moves_path} & setenv.bat & ' \
                  'java -Xmx512M gov.epa.otaq.moves.master.commandline.MOVESCommandLine -i {import_file}' \
                  ''.format(moves_path=self.path_moves, import_file=filename)
        os.system(command)

        # @TODO: change to use subprocess so output can be logged; for some reason subprocess doesn't work with multiple batch files - it only executes setenv.bat but never gets to {import_moves}.bat
        # output = subprocess.Popen(filename, cwd=self.path_moves, stdout=subprocess.PIPE).stdout.read()
        #
        # logger.debug('MOVES output: %s' % output)
