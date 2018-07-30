from Module import Module
from FPEAM import utils

import os
import pymysql
import pandas as pd
import numpy as np

LOGGER = utils.logger(name=__name__)

class MOVES(Module):
    def __init__(self, config, production, region_fips_map,
                 feedstock_measure_type, completed_moves_runs, year, **kvals):

        # init parent
        super(MOVES, self).__init__(config=config)

        # store input arguments in self
        self.production = production
        self.year = year
        self.region_fips_map = region_fips_map
        self.feedstock_measure_type = feedstock_measure_type

        # initialize empty list in which to store the MOVES runs already
        # completed
        # @todo check that this is the best way to record runs
        self.completed_moves_runs = completed_moves_runs

        # MOVES output database
        self.moves_output_db = config.get('moves_output_db')

        # open connection to MOVES default database for input/output
        self.moves_con = pymysql.connect(host=config.get('moves_db_host'),
                                         user=config.get('moves_db_user'),
                                         password=config.get('moves_db_pass'),
                                         db=config.get('moves_database'),
                                         local_infile=True)

        # input and output file directories - get paths from config
        self.moves_path = config.get('moves_path')
        self.moves_datafiles_path = config.get('moves_datafiles_path')

        # file-specific input directories - combine paths from config with
        # file-specific subdirectory names
        self.save_path_importfiles = os.path.join(self.moves_datafiles_path,
                                                  'import_files')
        self.save_path_runspecfiles = os.path.join(self.moves_datafiles_path,
                                                   'run_specs')
        self.save_path_countyinputs = os.path.join(self.moves_datafiles_path,
                                                   'county_inputs')
        self.save_path_nationalinputs = os.path.join(self.moves_datafiles_path,
                                                     'national_inputs')

        # file-specific output directory - combine paths from config with
        # file-specific subdirectory names
        self.save_path_outputs = os.path.join(self.moves_datafiles_path,
                                              'outputs')

        # list of file paths for MOVES inputs and outputs
        _path_list = [self.save_path_importfiles,
                      self.save_path_runspecfiles,
                      self.save_path_countyinputs,
                      self.save_path_nationalinputs,
                      self.save_path_outputs]

        # if file path does not exist, create it
        for _path in _path_list:
            if not os.path.exists(_path):
                os.makedirs(_path)

        # input and output databases - set names
        self.moves_database = config.get('moves_database')
        self.moves_output_db = config.get('moves_output_db')

        # user input - get toggle for running moves by state-level fips
        # finds FIPS with highest total (summed across feedstocks)
        # production in each state, runs MOVES only for those FIPS (50 FIPS)
        self.moves_state_level = config.get('state_level_moves')

        # user input - get toggle for running moves by feedstock and state
        # finds FIPS with highest production by feedstock in each state,
        # runs MOVES only
        # for those FIPS (50 x nfeedstock FIPS)
        self.moves_by_feedstock = config.get('moves_by_feedstock')

        # user input - default values used for running MOVES, actual VMT
        #  used to compute total emission in postprocessing
        self.vmt_short_haul = config.as_int('vmt_short_haul')

        # user input - population of combination short-haul trucks (assume one
        # per trip and only run MOVES for single trip)
        self.pop_short_haul = config.as_int('pop_short_haul')

        # user input - type of vehicle used to transport biomass
        self.hpmsv_type_id = config.get('hpmsv_type_id')

        # user input - subtype of vehicle used to transport biomass
        self.source_type_id = config.get('source_type_id')

        # engine technology used in biomass transport vehicle
        # '1' means a conventional internal combustion engine
        # @note possibly add to GUI as user input in the future
        # Currently only ONE engine technology can be selected at a time
        self.engine_tech = '1'

        # selection of fuels to run
        # 20 is conventional diesel and 21 is biodiesel
        # @note possibly add to GUI as user input in the future
        # the weird format is so it can be fed into a SQL query
        # can select additional fuel subtypes in list form
        self.fuel_subtype_id = '(20, 21)'

        # selection of fuel supply type
        # not sure what this means
        # @note possibly add to GUI as user input in the future
        self.fuel_supply_fuel_type_id = '2'

        # user input - fuel fraction table
        self.fuel_fraction = config.get('fuel_fraction')

        # user input - fraction of VMT on each road type
        self.vmt_fraction = config.get('vmt_fraction')

        # user input - timespan for which MOVES is run
        self.moves_timespan = config.get('moves_timespan')


    def __enter__(self):

        # @todo (?) open connection to MOVES database?

        return self


    def __exit__(self, exc_type, exc_val, exc_tb):

        # @todo close connection to MOVES database

        # process exceptions
        if exc_type is not None:
            LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self


    def create_national_data(self):
        """
        Create national data for MOVES, including:
            Alternate Vehicle Fuels & Technologies (avft)
            average speed distribution
            age distribution
            day VMT fraction
            month VMT fraction
            hour VMT fraction
            road type fraction

        This function only needs to be run once.

        :return: None
        """

        LOGGER.debug('Creating national data files for MOVES')

        # initialize kvals for string formatting
        kvals = dict()
        kvals['moves_database'] = self.moves_database
        kvals['source_type_id'] = self.source_type_id

        # export MOVES defaults for national inputs
        # hourVMTFraction, monthVMTFraction, dayVMTFraction,
        # and avgspeeddistribution
        _tables = ['hourvmtfraction', 'monthvmtfraction',
                   'dayvmtfraction', 'avgspeeddistribution']

        for _table in _tables:
            kvals['table'] = _table

            _table_sql = """SELECT * FROM {moves_database}.{table} WHERE
                     sourceTypeID = {source_type_id};""".format(
                     **kvals)

            # pull data from database and save in a csv
            pd.read_sql(_table_sql, self.moves_con).to_csv(os.path.join(
                self.save_path_nationalinputs, '%s.csv' % (kvals['table'],)),
                index=False)


        # alternative vehicle fuels and technology (avft) file creation
        # output should contain 182 rows (same as number of elements in
        # self.fuel_fraction)
        # @note HARDCODING ALERT
        # @note if source_type_id or engine_tech contain multiple elements,
        # this code will not create a usable avft file
        # @note DO NOT CHANGE data frame column names
        _avft_file = pd.DataFrame({'sourceTypeID':
                                       np.repeat(self.source_type_id,
                                                 self.fuel_fraction.__len__()),
                                   'modelYearID': np.repeat(range(1960, 2051),
                                                            2),
                                   'fuelTypeID': np.tile(range(1, 3),
                                                         0.5*self.fuel_fraction.__len__()),
                                   'engTechID': np.repeat(self.engine_tech,
                                                          self.fuel_fraction.__len__()),
                                   'fuelEngFraction': self.fuel_fraction})

        # write to csv
        _avft_file.to_csv(os.path.join(self.save_path_nationalinputs,
                                       'avft.csv'), sep=',')

        # default age distribution file creation
        # age distribution for user-specified source_type_id and year is pulled
        #  in from the MOVES database and written to file
        kvals['year'] = self.year

        _agedist_sql = """SELECT * FROM
        {moves_database}.sourcetypeagedistribution WHERE
        sourceTypeID = {source_type_id} AND yearID = {year};""".format(
            **kvals)

        # pull data from database and save in a csv
        pd.read_sql(_agedist_sql, self.moves_con).to_csv(os.path.join(
            self.save_path_nationalinputs,
            'default-age-distribution-tool-moves%s.csv' % (self.year,)),
            index=False)

        # create file for road type VMT fraction from user-specified VMT
        # fractions
        # @NOTE the format of vmt_fraction might cause problems - consider
        # switching to a list in the config file
        # @note DO NOT CHANGE data frame column names
        _roadtypevmt_filename = os.path.join(self.save_path_nationalinputs,
                                             'roadtype.csv')

        # construct dataframe of road type VMTs from config file input
        _roadtypevmt = pd.DataFrame({'sourceTypeID':
                                         np.repeat(self.source_type_id, 4),
                                     'roadTypeID': range(1, 5),
                                     'roadTypeVMTFraction': self.vmt_fraction})

        # write to csv
        _roadtypevmt.to_csv(_roadtypevmt_filename, sep=',', index=False)


    def create_county_data(self, fips):
        """

        Create county-level data for MOVES, including:
            vehicle miles travelled
            source type population
            fuel supply type
            fuel formulation
            fuel usage fraction
            meteorology

        County-level input files for MOVES that vary by FIPS, year,
        and feedstock

        :return: None
        """

        LOGGER.debug('Creating county-level data files for MOVES')

        # set up kvals for SQL query formatting
        kvals = dict()
        kvals['fips'] = fips
        kvals['year'] = self.year
        kvals['moves_database'] = self.moves_database
        kvals['fuel_subtype_id'] = self.fuel_subtype_id
        kvals['fuel_supply_fuel_type_id'] = self.fuel_supply_fuel_type_id
        kvals['countyID'] = str(int(fips))
        kvals['zoneID'] = str(int(fips)) + '0'

        # annual vehicle miles traveled by vehicle type
        # need one for each FIPS
        _vmt = pd.DataFrame({'HPMSVtypeID': self.hpmsv_type_id,
                             'yearID': self.year,
                             'HPMSBaseYearVMT': self.vmt_short_haul})

        # write vehicle miles travelec to file
        _vmt.to_csv(os.path.join(self.save_path_countyinputs,
                                '{fips}_vehiclemiletraveled_{'
                                'year}.csv'.format(**kvals)),
                    index=False)

        # source type population (number of vehicles by vehicle type)
        # need one for each fips
        _sourcetype = pd.DataFrame({'yearID': self.year,
                                    'sourceTypeID': self.source_type_id,
                                    'sourceTypePopulation':
                                        self.pop_short_haul})

        # write source type population to file
        _sourcetype.to_csv(os.path.join(self.save_path_countyinputs,
                                       '{fips}_sourcetype_{'
                                       'year}.csv'.format(**kvals)),
                           index=False)

        # export county-level fuel supply data
        # need one for each FIPS
        _fuelsupply_sql = """SELECT * FROM {moves_database}.fuelsupply
                            WHERE {moves_database}.fuelsupply.fuelRegionID =
                            (SELECT DISTINCT regionID FROM {
                            moves_database}.regioncounty WHERE countyID = '{
                            countyID}' AND fuelYearID = '{year}')
                            AND {moves_database}.fuelsupply.fuelYearID = '{
                            year}'""".format(**kvals)

        # pull data from database and save in a csv
        pd.read_sql(_fuelsupply_sql, self.moves_con).to_csv(os.path.join(
            self.save_path_countyinputs, '{fips}_fuelsupply_{'
                                         'year}.csv'.format(**kvals)))

        # export county-level fuel formulation data
        # need one for each FIPS-year combination
        _fuelform_sql = """SELECT * FROM {moves_database}.fuelformulation
                            WHERE {moves_database}.fuelformulation.fuelSubtypeID
                            IN {fuel_subtype_id};""".format(**kvals)

        # pull data from database and save in a csv
        pd.read_sql(_fuelform_sql, self.moves_con).to_csv(os.path.join(
            self.save_path_countyinputs, '{fips}_fuelformulation_{'
                                         'year}.csv'.format(**kvals)))

        # export county-level fuel usage fraction data
        # need one for each FIPS-year combination
        _fuelusagename_sql = """SELECT * FROM {moves_database}.fuelusagefraction
                            WHERE {moves_database}.fuelusagefraction.countyID =
                            '{countyID}' AND
                            {moves_database}.fuelusagefraction.fuelYearID =
                            '{year}' AND
                            {moves_database}.fuelusagefraction.fuelSupplyFuelTypeID =
                            {fuel_supply_fuel_type_id};""".format(**kvals)

        # pull data from database and save in a csv
        pd.read_sql(_fuelusagename_sql, self.moves_con).to.csv(os.path.join(
            self.save_path_countyinputs, '{fips}_fuelusagefraction_{'
                                         'year}.csv'.format(**kvals)))

        # export county-level meteorology data
        # need one for each FIPS
        _met_sql = """SELECT * FROM {moves_database}.zonemonthhour WHERE {
        moves_database}.zonemonthhour.zoneID = {zoneID}""".format(**kvals)

        # pull data from database and save in a csv
        pd.read_sql(_met_sql, self.moves_con).to_csv(os.path.join(
            self.save_path_countyinputs, '%s_met.csv' % (fips, )))


    def create_xml_import(self):
        """
        Create and save XML import files for running MOVES
        :return: None
        """
        pass


    def create_xml_runspec(self):
        """
        Create and save XML runspec files for running MOVES
        :return: None
        """
        pass


    def create_batch_files(self):
        """
        Create and save batch files for running MOVES
        :return: None
        """
        pass


    def run_moves(self):
        """
        Calls all necessary methods to do preprocessing, setup MOVES input
        files, run MOVES via command line, and postprocess output
        :return:
        """

        # first, generate a list of FIPS-state combinations for which MOVES
        # will be run

        # add a column with the state code to the region-to-fips df
        self.region_fips_map['MOVES_state'] = \
            self.region_fips_map.MOVES_fips.str[0:2]

        # merge the feedstock_measure_type rows from production with the
        # region-FIPS map
        _prod_merge = self.production[
            self.production.feedstock_measure ==
            self.feedstock_measure_type].merge(
            self.region_fips_map, on='region_production')

        # sum all feedstock production within each FIPS-year combo (also
        # grouping by state just pulls that column along, it doesn't change
        # the grouping)
        _amts_by_fips_feed = _prod_merge.groupby(['MOVES_fips',
                                                  'MOVES_state',
                                                  'feedstock'],
                                                 as_index=False).sum()

        # within each FIPS-year-feedstock combo, find the highest
        # feedstock production
        _max_amts_feed = _amts_by_fips_feed.groupby(['MOVES_state',
                                                     'feedstock'],
                                                    as_index=False).max()

        if self.moves_state_level:

            # sum total feedstock production within each fips-state-year combo
            _amts_by_fips = _amts_by_fips_feed.groupby(['MOVES_fips',
                                                        'MOVES_state'],
                                                       as_index=False).sum()

            # locate the fips within each state with the highest total
            # feedstock production
            _max_amts = _amts_by_fips.groupby(['MOVES_state'],
                                              as_index=False).max()

            # strip out duplicates (shouldn't be any) to create a list of
            # unique fips-state-year combos to run MOVES on
            self.moves_run_combos = _max_amts[['MOVES_fips',
                                               'MOVES_state']].drop_duplicates()

        elif self.moves_by_feedstock:

            # get a list of unique fips-state-year combos to run MOVES on
            self.moves_run_combos = _max_amts_feed[['MOVES_fips',
                                                    'MOVES_state']].drop_duplicates()

        else:

            # if neither moves_state_level nor moves_by_feedstock are True,
            # the fips-state-year combos to run MOVES on come straight from
            # the production data
            self.moves_run_combos = _prod_merge[['MOVES_fips',
                                                 'MOVES_state']].drop_duplicates()

        self.moves_run_combos['year'] = self.year

        # @note moves_run_combos is being stored in self as a potential
        # output or check on functionality

        # after generating the list of FIPS over which MOVES is run,
        # begin to create the input data and run MOVES

        # create national datasets only once per FPEAM
        self.create_national_data()

        # loop thru rows of moves_run_combos to generate input data files
        # for each FIPS
        for i in self.moves_run_combos.shape[0]:

            # create county-level data files
            self.create_county_data(fips=self.moves_run_combos.fips[i])

            # create XML import files
            self.create_xml_import()

            # create XML run spec files
            self.create_xml_runspec()

            # create batch files for importing and running MOVES
            self.create_batch_files()
            batch_run_dict = None

        # actually send the command to run MOVES
        for fips in self.moves_run_combos.fips:

            # check if batch run dictionary contains any files
            # @todo batch_run_dict is a list of the batch run file (names
            # and paths?)

            if batch_run_dict[fips] is not None:

                # if so, execute batch file and log output
                LOGGER.info('Running MOVES for fips: %s' % (fips))
                LOGGER.info('Batch file MOVES for importing data: %s' % (
                    batch_run_dict[fips], ))

                command = 'cd {moves_folder} & setenv.bat & '\
                          'java -Xmx512M '\
                          'gov.epa.otaq.moves.master.commandline.MOVESCommandLine'\
                          '-r {run_moves}'.format(moves_folder=self.moves_path,
                                                  run_moves=batch_run_dict[
                                                      fips])
                os.system(command)

                # @note this is a stopgap way to record which MOVES runs
                # have been completed
                self.completed_moves_runs.append("{fips}_{year}".format(
                    fips=fips, year = self.year))

            else:

                # otherwise, report that MOVES run already complete
                LOGGER.info('MOVES run already complete for fips: %s' % (fips))

        # postprocess output - outside the loop
        self.moves_postprocess()


## POSTPROCESS MOVES OUTPUT ##


    def moves_postprocess(self):
        """

        :return: None
        """
        pass