import csv
import os
import time

import numpy as np
import pandas as pd
import pymysql
from Module import Module
from lxml import etree
from lxml.builder import E

from FPEAM import utils

LOGGER = utils.logger(name=__name__)

# @TODO keep the movesscenarioID in output table to identify cached results
# @TODO separate directories for separate scenario names, also tack on
# scenario name to MOVES input file names


class MOVES(Module):

    def __init__(self, config, production, region_fips_map,
                 feedstock_measure_type, truck_capacity, completed_moves_runs,
                 year, **kvals):

        # init parent
        super(MOVES, self).__init__(config=config)

        # store input arguments in self
        self.production = production
        self.year = year
        self.region_fips_map = region_fips_map
        self.feedstock_measure_type = feedstock_measure_type

        # this is a DF read in from a csv file
        self.truck_capacity = truck_capacity

        # initialize empty list in which to store the MOVES runs already completed
        # @TODO how should completed MOVES runs be recorded?
        self.completed_moves_runs = completed_moves_runs

        self.use_cached_results = config.get('use_cached_results')

        # scenario name
        # @TODO update to match the correct name in the config file
        self.model_run_title = config.get('scenario_name')

        # MOVES output database
        self.moves_output_db = config.get('moves_output_db')

        # open connection to MOVES default database for input/output
        self.moves_con = pymysql.connect(host=config.get('moves_db_host'),
                                         user=config.get('moves_db_user'),
                                         password=config.get('moves_db_pass'),
                                         db=config.get('moves_database'),
                                         local_infile=True)

        # creates cursor for executing queries within the MOVES database (
        # not reading in data, altering tables
        self.moves_cursor = self.moves_con.cursor()

        # get version of MOVES for XML trees
        self.moves_version = config.get('moves_version')

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

        # additional input file paths
        self.avft_filename = os.path.join(self.save_path_nationalinputs,
                                          'avft.csv')
        self.setenv_file = os.path.join(self.moves_path, 'setenv.bat')

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

        # parameters for generating XML runspec files for MOVES
        # month(s) for analysis
        self.mo = self.moves_timespan['mo']
        # days(s) for analysis
        self.d = self.moves_timespan['d']
        # beginning hour(s) for analysis
        self.bhr = self.moves_timespan['bhr']
        # ending hour(s) for analysis
        self.ehr = self.moves_timespan['ehr']

        # machine where MOVES output db lives
        self.server = config.get('moves_db_host')

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
        # @NOTE possibly add to GUI as user input in the future
        # Currently only ONE engine technology can be selected at a time
        self.engine_tech = '1'

        # selection of fuels to run
        # 20 is conventional diesel and 21 is biodiesel
        # @NOTE possibly add to GUI as user input in the future
        # the weird format is so it can be fed into a SQL query
        # can select additional fuel subtypes in list form
        self.fuel_subtype_id = '(20, 21)'

        # selection of fuel supply type
        # not sure what this means
        # @NOTE possibly add to GUI as user input in the future
        self.fuel_supply_fuel_type_id = '2'

        # user input - fuel fraction table
        self.fuel_fraction = config.get('fuel_fraction')

        # user input - fraction of VMT on each road type
        self.vmt_fraction = config.get('vmt_fraction')

        # user input - timespan for which MOVES is run
        self.moves_timespan = config.get('moves_timespan')

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
        # @NOTE HARDCODING ALERT
        # @NOTE if source_type_id or engine_tech contain multiple elements,
        # this code will not create a usable avft file
        # @NOTE DO NOT CHANGE data frame column names
        _avft_file = pd.DataFrame({'sourceTypeID': np.repeat(self.source_type_id,
                                                             self.fuel_fraction.__len__()),
                                   'modelYearID': np.repeat(range(1960, 2051),
                                                            2),
                                   'fuelTypeID': np.tile(range(1, 3),
                                                         0.5 * self.fuel_fraction.__len__()),
                                   'engTechID': np.repeat(self.engine_tech,
                                                          self.fuel_fraction.__len__()),
                                   'fuelEngFraction': self.fuel_fraction})

        # write to csv
        _avft_file.to_csv(self.avft_filename, sep=',')

        # default age distribution file creation
        # age distribution for user-specified source_type_id and year is pulled
        #  in from the MOVES database and written to file
        kvals['year'] = self.year

        _agedist_sql = """SELECT * FROM
        {moves_database}.sourcetypeagedistribution WHERE
        sourceTypeID = {source_type_id} AND yearID = {year};""".format(
                **kvals)

        # save this file name to self so it can be used by create_xml_import
        self.agedistfilename = os.path.join(
                self.save_path_nationalinputs,
                'default-age-distribution-tool-moves%s.csv' % (self.year,))

        # pull data from database and save in a csv
        pd.read_sql(_agedist_sql, self.moves_con).to_csv(self.agedistfilename,
                                                         index=False)

        # create file for road type VMT fraction from user-specified VMT
        # fractions
        # @NOTE the format of vmt_fraction might cause problems - consider
        # switching to a list in the config file
        # @NOTE DO NOT CHANGE data frame column names
        self.roadtypevmt_filename = os.path.join(self.save_path_nationalinputs, 'roadtype.csv')

        # construct dataframe of road type VMTs from config file input
        # store in self for later use in postprocessing
        self.roadtypevmt = pd.DataFrame({'sourceTypeID': np.repeat(self.source_type_id, 4),
                                         'roadTypeID': range(1, 5),
                                         'roadTypeVMTFraction':
                                             self.vmt_fraction})

        # write to csv
        self.roadtypevmt.to_csv(self.roadtypevmt_filename, sep=',',
                                index=False)

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

        # @NOTE the name is FIPS dependent, cannot be created in init
        self.vmt_filename = os.path.join(self.save_path_countyinputs,
                                         '{fips}_vehiclemiletraveled_{'
                                         'year}.csv'.format(**kvals))

        # write vehicle miles travelec to file
        _vmt.to_csv(self.vmt_filename, index=False)

        # source type population (number of vehicles by vehicle type)
        # need one for each fips
        _sourcetype = pd.DataFrame({'yearID': self.year,
                                    'sourceTypeID': self.source_type_id,
                                    'sourceTypePopulation':
                                        self.pop_short_haul})

        # @NOTE the name is FIPS dependent, cannot be created in init
        self.sourcetype_filename = os.path.join(self.save_path_countyinputs,
                                                '{fips}_sourcetype_{'
                                                'year}.csv'.format(**kvals))

        # write source type population to file
        _sourcetype.to_csv(self.sourcetype_filename, index=False)

        # export county-level fuel supply data
        # need one for each FIPS
        _fuelsupply_sql = """SELECT * FROM {moves_database}.fuelsupply
                            WHERE {moves_database}.fuelsupply.fuelRegionID =
                            (SELECT DISTINCT regionID FROM {
                            moves_database}.regioncounty WHERE countyID = '{
                            countyID}' AND fuelYearID = '{year}')
                            AND {moves_database}.fuelsupply.fuelYearID = '{
                            year}'""".format(**kvals)

        # save for later use in create_xml_imports
        self.fuelsupply_filename = os.path.join(self.save_path_countyinputs,
                                                '{fips}_fuelsupply_{'
                                                'year}.csv'.format(**kvals))

        # pull data from database and save in a csv
        pd.read_sql(_fuelsupply_sql,
                    self.moves_con).to_csv(self.fuelsupply_filename)

        # export county-level fuel formulation data
        # need one for each FIPS-year combination
        _fuelform_sql = """SELECT * FROM {moves_database}.fuelformulation
                            WHERE {moves_database}.fuelformulation.fuelSubtypeID
                            IN {fuel_subtype_id};""".format(**kvals)

        # @NOTE the name is FIPS dependent, cannot be created in init
        self.fuelformulation_filename = os.path.join(
                self.save_path_countyinputs, '{fips}_fuelformulation_{'
                                             'year}.csv'.format(**kvals))

        # pull data from database and save in a csv
        pd.read_sql(_fuelform_sql,
                    self.moves_con).to_csv(self.fuelformulation_filename)

        # export county-level fuel usage fraction data
        # need one for each FIPS-year combination
        _fuelusagename_sql = """SELECT * FROM {moves_database}.fuelusagefraction
                            WHERE {moves_database}.fuelusagefraction.countyID =
                            '{countyID}' AND
                            {moves_database}.fuelusagefraction.fuelYearID =
                            '{year}' AND
                            {moves_database}.fuelusagefraction.fuelSupplyFuelTypeID =
                            {fuel_supply_fuel_type_id};""".format(**kvals)

        # @NOTE the name is FIPS dependent, cannot be created in init
        self.fuelusage_filename = os.path.join(self.save_path_countyinputs,
                                               '{fips}_fuelusagefraction_{'
                                               'year}.csv'.format(**kvals))

        # pull data from database and save in a csv
        pd.read_sql(_fuelusagename_sql,
                    self.moves_con).to.csv(self.fuelusage_filename)

        # export county-level meteorology data
        # need one for each FIPS
        _met_sql = """SELECT * FROM {moves_database}.zonemonthhour WHERE {
        moves_database}.zonemonthhour.zoneID = {zoneID}""".format(**kvals)

        # @NOTE the name is FIPS dependent, cannot be created in init
        self.met_filename = os.path.join(self.save_path_countyinputs,
                                         '{fips}_met.csv'.format(**kvals))

        # pull data from database and save in a csv
        pd.read_sql(_met_sql, self.moves_con).to_csv(self.met_filename)

    def create_xml_import(self, fips):
        """

        Create and save XML import files for running MOVES

        :return: None
        """

        # assemble kvals dict for string & filepath formatting
        kvals = dict()
        kvals['fips'] = fips
        kvals['year'] = self.year

        # set parser to leave CDATA sections in document
        self.parser = etree.XMLParser(strip_cdata=False, recover=True)

        # create these files here since they were generated in a loop in
        # create_national_inputs - no stored filename
        # path to average speed distribution file (national inputs)
        _avgspeeddist_filename = os.path.join(self.save_path_nationalinputs,
                                              'avgspeeddistribution')
        _month_vmt_filename = os.path.join(self.save_path_nationalinputs,
                                           'monthvmtfraction')
        _day_vmt_filename = os.path.join(self.save_path_nationalinputs,
                                         'dayvmtfraction')
        _hour_vmt_filename = os.path.join(self.save_path_nationalinputs,
                                          'hourvmtfraction')

        # create XML for elements with CDATA
        self.internalcontrol = etree.XML(
                '<internalcontrolstrategy classname="gov.epa.otaq.moves.master.implementation.'
                'ghg.internalcontrolstrategies.rateofprogress.RateOfProgressStrategy">'
                '<![CDATA[useParameters	No]]></internalcontrolstrategy>',
                self.parser)
        self.agename = "<filename>{agedistfilename}</filename>".format(
                agedistfilename=self.agedistfilename)
        self.agefile = etree.XML(self.agename, self.parser)
        self.speedfile = etree.XML(
                "<filename>{speedfilename}</filename>".format(
                        speedfilename=_avgspeeddist_filename), self.parser)
        self.fuelsupfile = etree.XML(
                "<filename>{fuelsupfilename}</filename>".format(
                        fuelsupfilename=self.fuelsupply_filename), self.parser)
        self.fuelformfile = etree.XML(
                "<filename>{fuelformfilename}</filename>".format(
                        fuelformfilename=self.fuelformulation_filename), self.parser)
        self.fuelusagefile = etree.XML(
                "<filename>{fuelusagefilename}</filename>".format(
                        fuelusagefilename=self.fuelusage_filename), self.parser)
        self.avftfile = etree.XML("<filename>{avftfilename}</filename>".format(
                avftfilename=self.avft_filename), self.parser)
        self.metfile = etree.XML("<filename>{metfilename}</filename>".format(
                metfilename=self.met_filename), self.parser)
        self.roadtypefile = etree.XML(
                "<filename>{roadtypefilename}</filename>".format(
                        roadtypefilename=self.roadtypevmt_filename), self.parser)
        self.sourcetypefile = etree.XML(
                "<filename>{sourcetypefilename}</filename>".format(
                        sourcetypefilename=self.sourcetype_filename), self.parser)
        self.HPMSyearfile = etree.XML(
                "<filename>{vmtfilename}</filename>".format(
                        vmtfilename=self.vmt_filename), self.parser)
        self.monthVMTfile = etree.XML(
                "<filename>{monthvmtfilename}</filename>".format(
                        monthvmtfilename=_month_vmt_filename), self.parser)
        self.dayVMTfile = etree.XML(
                "<filename>{dayvmtfilename}</filename>".format(
                        dayvmtfilename=_day_vmt_filename), self.parser)
        self.hourVMTfile = etree.XML(
                "<filename>{hourvmtfilename}</filename>".format(
                        hourvmtfilename=_hour_vmt_filename), self.parser)

        # input database
        self.db_in = "fips_{fips}_{year}_in".format(fips=fips,
                                                    year=self.year)
        # scenario ID for MOVES runs
        # ends up in tables in the MOVES output database
        self.scenid = "{fips}_{year}_{month}_{day}".format(fips=fips,
                                                           day=self.d,
                                                           month=self.mo,
                                                           year=self.year)

        # Create XML element tree for geographic selection

        # XML for geographic selection
        geoselect = etree.Element("geographicselection", type="COUNTY")
        geoselect.set("key", fips)
        geoselect.set("description", "")

        # Create XML element tree for MOVES timespan

        # XML for timespan
        timespan = etree.Element("timespan")

        # set year
        etree.SubElement(timespan, "year", key=self.year)

        # loop through months
        for months in self.mo:
            etree.SubElement(timespan, "month", id=months)

        # loop through days (2 = weekend; 5 = weekday)
        for days in self.d:
            etree.SubElement(timespan, "day", id=days)

        # loop through start hours
        for hours in self.bhr:
            etree.SubElement(timespan, "beginhour", id=hours)

        # loop through end hours
        for hours in self.ehr:
            etree.SubElement(timespan, "endhour", id=hours)

        # aggregate at hourly level
        etree.SubElement(timespan, "aggregateBy", key="Hour")

        # Create XML element tree for MOVES vehicle type
        # @NOTE Currently only for combination short-haul truck

        # XML for vehicle type selections
        # combination short-haul truck
        # @TODO convert all of these to user inputs pulled from config
        vehicle_selection = etree.Element("onroadvehicleselection",
                                          fueltypeid=self.fuel_supply_fuel_type_id)
        vehicle_selection.set("fueltypedesc", "Diesel Fuel")
        vehicle_selection.set("sourcetypeid", self.source_type_id)
        vehicle_selection.set("sourcetypename", "Combination Short-haul Truck")

        # Create XML element tree for MOVES pollutant processes
        # Currently includes: CO, NH3, PM10, PM2.5, SO2, NOX, VOC,
        # and prerequisites

        # dictionary of pollutant shorthand to MOVES name
        _polname = {"NH3": "Ammonia (NH3)",
                    "CO": "Carbon Monoxide (CO)",
                    "ECPM": "Composite - NonECPM",
                    "Carbon": "Elemental Carbon",
                    "H20": "H20 (aerosol)",
                    "NMHC": "Non-Methane Hydrocarbons",
                    "NOX": "Oxides of Nitrogen",
                    "PM10": "Primary Exhaust PM10  - Total",
                    "PM25": "Primary Exhaust PM2.5 - Total",
                    "Spar": "Sulfur Particulate",
                    "SO2": "Sulfur Dioxide (SO2)",
                    "TEC": "Total Energy Consumption",
                    "THC": "Total Gaseous Hydrocarbons",
                    "VOC": "Volatile Organic Compounds"}

        # dictionary of pollutant shorthand to MOVES pollutantid
        _polkey = {"NH3": "30",
                   "CO": "2",
                   "ECPM": "118",
                   "Carbon": "112",
                   "H20": "119",
                   "NMHC": "79",
                   "NOX": "3",
                   "PM10": "100",
                   "PM25": "110",
                   "Spar": "115",
                   "SO2": "31",
                   "TEC": "91",
                   "THC": "1",
                   "VOC": "87"}

        # dictionary of MOVES pollutant process numbers to MOVES pollutant process descriptions
        _procname = {"1": "Running Exhaust",
                     "2": "Start Exhaust",
                     "11": "Evap Permeation",
                     "12": "Evap Fuel Vapor Venting",
                     "13": "Evap Fuel Leaks",
                     "15": "Crankcase Running Exhaust",
                     "16": "Crankcase Start Exhaust",
                     "17": "Crankcase Extended Idle Exhaust",
                     "18": "Refueling Displacement Vapor Loss",
                     "19": "Refueling Spillage Loss",
                     "90": "Extended Idle Exhaust",
                     "91": "Auxiliary Power Exhaust"}

        # dictionary of shorthand pollutant names to applicable MOVES pollutant process numbers
        _prockey = {"NH3": ["1", "2", "15", "16", "17", "90", "91"],
                    "CO": ["1", "2", "15", "16", "17", "90", "91"],
                    "ECPM": ["1", "2", "90", "91"],
                    "Carbon": ["1", "2", "90", "91"],
                    "H20": ["1", "2", "90", "91"],
                    "NMHC": ["1", "2", "11", "12", "13", "18", "19", "90",
                             "91"],
                    "NOX": ["1", "2", "15", "16", "17", "90", "91"],
                    "PM10": ["1", "2", "15", "16", "17", "90", "91"],
                    "PM25": ["1", "2", "15", "16", "17", "90", "91"],
                    "Spar": ["1", "2", "90", "91"],
                    "SO2": ["1", "2", "15", "16", "17", "90", "91"],
                    "TEC": ["1", "2", "90", "91"],
                    "THC": ["1", "2", "11", "12", "13", "18", "19", "90", "91"],
                    "VOC": ["1", "2", "11", "12", "13", "15", "16", "17", "18",
                            "19", "90", "91"]}

        # XML for pollutant process associations
        # create element for pollutant process associations
        polproc = etree.Element("pollutantprocessassociations")

        # populate subelements for pollutant processes
        # loop through all pollutants
        for _pol in _polname:
            # loop through all processes associated with each pollutant
            for _proc in _prockey[_pol]:
                pollutant = etree.SubElement(polproc,
                                             "pollutantprocessassociation",
                                             pollutantkey=_polkey[_pol])
                pollutant.set("pollutantname", _polname[_pol])
                pollutant.set("processkey", _proc)
                pollutant.set("processname", _procname[_proc])

        # Create XML element tree for MOVES road types

        # dictionary for road types
        roaddict = {"1": "Off-Network",
                    "2": "Rural Restricted Access",
                    "3": "Rural Unrestricted Access",
                    "4": "Urban Restricted Access",
                    "5": "Urban Unrestricted Access"}

        # XML for road types
        roadtypes = etree.Element("roadtypes", {"separateramps": "false"})
        for roads in roaddict:
            roadtype = etree.SubElement(roadtypes, "roadtype",
                                        roadtypeid=roads)
            roadtype.set("roadtypename", roaddict[roads])
            roadtype.set("modelCombination", "M1")

        # Create XML element tree for MOVES input database information

        # XML for database selection
        databasesel = etree.Element("databaseselection",
                                    servername=self.server)
        databasesel.set("databasename", self.db_in)

        # Create XML element tree for MOVES vehicle age distribution

        # XML for age distribution
        agedist = etree.Element("agedistribution")
        etree.SubElement(agedist, "description")
        part = etree.SubElement(agedist, "parts")
        std = etree.SubElement(part, "sourceTypeAgeDistribution")
        etree.SubElement(std, "filename")

        # Create full element tree for MOVES import file
        importfilestring = (
            E.moves(
                    E.importer(
                            E.filters(
                                    E.geographicselections(geoselect),
                                    timespan,
                                    E.onroadvehicleselections(vehicle_selection),
                                    E.offroadvehicleselections(""),
                                    E.offroadvehiclesccs(""),
                                    roadtypes,
                                    polproc,
                            ),
                            databasesel,
                            E.agedistribution(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(E.sourceTypeAgeDistribution(self.agefile))),
                            E.avgspeeddistribution(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(E.avgSpeedDistribution(self.speedfile))),
                            E.fuel(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(
                                            E.FuelSupply(self.fuelsupfile),
                                            E.FuelFormulation(self.fuelformfile),
                                            E.FuelUsageFraction(self.fuelusagefile),
                                            E.AVFT(self.avftfile),
                                    )),
                            E.zoneMonthHour(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(E.zonemonthhour(self.metfile))),
                            E.rampfraction(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(E.roadType(E.filename("")))),
                            E.roadtypedistribution(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(E.roadTypeDistribution(self.roadtypefile))),
                            E.sourcetypepopulation(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(E.sourceTypeYear(self.sourcetypefile))),
                            E.starts(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(
                                            E.startsPerDay(E.filename("")),
                                            E.startsHourFraction(E.filename("")),
                                            E.startsSourceTypeFraction(E.filename("")),
                                            E.startsMonthAdjust(E.filename("")),
                                            E.importStartsOpModeDistribution(E.filename("")),
                                            E.Starts(E.filename("")),
                                    )),
                            E.vehicletypevmt(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(
                                            E.HPMSVtypeYear(self.HPMSyearfile),
                                            E.monthVMTFraction(self.monthVMTfile),
                                            E.dayVMTFraction(self.dayVMTfile),
                                            E.hourVMTFraction(self.hourVMTfile),
                                    )),
                            E.hotelling(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(
                                            E.hotellingActivityDistribution(E.filename("")),
                                            E.hotellingHours(E.filename("")))),
                            E.imcoverage(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(E.IMCoverage(E.filename("")))),
                            E.onroadretrofit(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(E.onRoadRetrofit(E.filename("")))),
                            E.generic(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              self.parser),
                                    E.parts(E.anytable(E.tablename("agecategory"),
                                                       E.filename("")))),
                            # @TODO have mode be set by user input?
                            mode="county")
            )
        )

        # Transform element tree to string and save to file

        # create string from element tree
        stringout = etree.tostring(importfilestring, pretty_print=True,
                                   encoding='utf8')

        # create import filename using FIPS code, crop, and scenario year
        _im_filename = os.path.join(self.save_path_importfiles,
                                    '{fips}_import_{year}.mrs'.format(
                                            fips=fips, year=self.year))

        # save string to file
        fileout = open(_im_filename, "w")
        fileout.write(stringout)
        fileout.close()

    def create_xml_runspec(self, fips):
        """
        Create and save XML runspec files for running MOVES
        :return: None
        """

        # set parser to leave CDATA sections in document
        _parser = etree.XMLParser(strip_cdata=False)

        # scenario ID for MOVES runs
        _scenid = "{fips}_{year}_{month}_{day}".format(fips=fips,
                                                       day=self.d[0],
                                                       month=self.mo[0],
                                                       year=self.year)

        # Create XML element tree for elements with MOVES inputs with CDATA
        description = etree.XML('<description><![CDATA[]]></description>',
                                _parser)
        internalcontrol = etree.XML(
                '<internalcontrolstrategy classname="gov.epa.otaq.moves.master.implementation.ghg.'
                'internalcontrolstrategies.rateofprogress.RateOfProgressStrategy">'
                '<![CDATA[useParameters	No]]></internalcontrolstrategy>',
                _parser)

        # Create XML element tree for MOVES uncertainty parameters
        uncertaintyparam = etree.Element("uncertaintyparameters",
                                         uncertaintymodeenabled="false")
        uncertaintyparam.set("numberofrunspersimulation", "0")
        uncertaintyparam.set("numberofsimulations", "0")

        # Create XML element tree for MOVES output emissions breakdown,
        # which specifies which outputs are included in MOVES analysis
        outputemissions = etree.Element(
                "outputemissionsbreakdownselection")
        etree.SubElement(outputemissions, "modelyear", selected="false")
        etree.SubElement(outputemissions, "fueltype", selected="false")
        etree.SubElement(outputemissions, "fuelsubtype", selected="false")
        etree.SubElement(outputemissions, "emissionprocess",
                         selected="true")
        etree.SubElement(outputemissions, "onroadoffroad", selected="true")
        etree.SubElement(outputemissions, "roadtype", selected="true")
        etree.SubElement(outputemissions, "sourceusetype",
                         selected="false")
        etree.SubElement(outputemissions, "movesvehicletype",
                         selected="false")
        etree.SubElement(outputemissions, "onroadscc", selected="false")
        estimateduncer = etree.SubElement(outputemissions,
                                          "estimateuncertainty",
                                          selected="false")
        estimateduncer.set("numberOfIterations", "2")
        estimateduncer.set("keepSampledData", "false")
        estimateduncer.set("keepIterations", "false")
        etree.SubElement(outputemissions, "sector", selected="false")
        etree.SubElement(outputemissions, "engtechid", selected="false")
        etree.SubElement(outputemissions, "hpclass", selected="false")
        etree.SubElement(outputemissions, "regclassid", selected="false")

        # Create XML element tree for MOVES output database information
        outputdatabase = etree.Element("outputdatabase",
                                       servername=self.server)
        outputdatabase.set("databasename", self.moves_output_db)
        outputdatabase.set("description", "")

        # Create XML element tree for MOVES input database information
        scaleinput = etree.Element("scaleinputdatabase",
                                   servername=self.server)
        scaleinput.set("databasename",
                       "fips_{fips}_{year}_in".format(fips=fips,
                                                      year=self.year))
        scaleinput.set("description", "")

        # Create XML element tree for units used for MOVES output
        outputfactors = etree.Element("outputfactors")
        timefac = etree.SubElement(outputfactors, "timefactors",
                                   selected="true")
        timefac.set("units", "Hours")
        disfac = etree.SubElement(outputfactors, "distancefactors",
                                  selected="true")
        disfac.set("units", "Miles")
        massfac = etree.SubElement(outputfactors, "massfactors",
                                   selected="true")
        massfac.set("units", "Grams")
        massfac.set("energyunits", "Joules")

        # Create XML element trees for other MOVES runspec inputs

        # generate database with other outputs (leave empty)
        gendata = etree.Element("generatordatabase", shouldsave="false")
        gendata.set("servername", "")
        gendata.set("databasename", "")
        gendata.set("description", "")

        # lookupflags for database
        lookupflag = etree.Element("lookuptableflags",
                                   scenarioid=_scenid)
        lookupflag.set("truncateoutput", "true")
        lookupflag.set("truncateactivity", "true")
        lookupflag.set("truncatebaserates", "true")

        # Create XML element tree for MOVES geographic selection
        geoselect = etree.Element("geographicselection", type="COUNTY")
        geoselect.set("key", fips)
        geoselect.set("description", "")

        # Create XML element tree for MOVES timespan

        # XML for timespan
        timespan = etree.Element("timespan")
        # set year
        etree.SubElement(timespan, "year", key=self.year)
        # loop through months
        for months in self.mo:
            etree.SubElement(timespan, "month", id=months)
        # loop through days (2 = weekend; 5 = weekday)
        for days in self.d:
            etree.SubElement(timespan, "day", id=days)
        # loop through start hours
        for hours in self.bhr:
            etree.SubElement(timespan, "beginhour", id=hours)
        # loop through end hours
        for hours in self.ehr:
            etree.SubElement(timespan, "endhour", id=hours)
        # aggregate at hourly level
        etree.SubElement(timespan, "aggregateBy", key="Hour")

        # Create XML element tree for MOVES vehicle type
        # @TODO connect all of these items back to user input
        # @NOTE can lists instead of individual types be specified here -
        # for running multiple vehicle types?
        # XML for vehicle type selections
        # combination short-haul truck
        vehicle_selection = etree.Element("onroadvehicleselection",
                                          fueltypeid=self.fuel_supply_fuel_type_id)
        vehicle_selection.set("fueltypedesc", "Diesel Fuel")
        vehicle_selection.set("sourcetypeid", self.source_type_id)
        vehicle_selection.set("sourcetypename", "Combination Short-haul Truck")

        # Create XML element tree for MOVES pollutant processes
        # Currently includes: CO, NH3, PM10, PM2.5, SO2, NOX, VOC,
        # and prerequisites

        # dictionary of pollutant shorthand to MOVES name
        _polname = {"NH3": "Ammonia (NH3)",
                    "CO": "Carbon Monoxide (CO)",
                    "ECPM": "Composite - NonECPM",
                    "Carbon": "Elemental Carbon",
                    "H20": "H20 (aerosol)",
                    "NMHC": "Non-Methane Hydrocarbons",
                    "NOX": "Oxides of Nitrogen",
                    "PM10": "Primary Exhaust PM10  - Total",
                    "PM25": "Primary Exhaust PM2.5 - Total",
                    "Spar": "Sulfur Particulate",
                    "SO2": "Sulfur Dioxide (SO2)",
                    "TEC": "Total Energy Consumption",
                    "THC": "Total Gaseous Hydrocarbons",
                    "VOC": "Volatile Organic Compounds"}

        # dictionary of pollutant shorthand to MOVES pollutantid
        _polkey = {"NH3": "30",
                   "CO": "2",
                   "ECPM": "118",
                   "Carbon": "112",
                   "H20": "119",
                   "NMHC": "79",
                   "NOX": "3",
                   "PM10": "100",
                   "PM25": "110",
                   "Spar": "115",
                   "SO2": "31",
                   "TEC": "91",
                   "THC": "1",
                   "VOC": "87"}

        # dictionary of MOVES pollutant process numbers to MOVES pollutant
        # process descriptions
        _procname = {"1": "Running Exhaust",
                     "2": "Start Exhaust",
                     "11": "Evap Permeation",
                     "12": "Evap Fuel Vapor Venting",
                     "13": "Evap Fuel Leaks",
                     "15": "Crankcase Running Exhaust",
                     "16": "Crankcase Start Exhaust",
                     "17": "Crankcase Extended Idle Exhaust",
                     "18": "Refueling Displacement Vapor Loss",
                     "19": "Refueling Spillage Loss",
                     "90": "Extended Idle Exhaust",
                     "91": "Auxiliary Power Exhaust"}

        # dictionary of shorthand pollutant names to applicable MOVES
        # pollutant process numbers
        _prockey = {"NH3": ["1", "2", "15", "16", "17", "90", "91"],
                    "CO": ["1", "2", "15", "16", "17", "90", "91"],
                    "ECPM": ["1", "2", "90", "91"],
                    "Carbon": ["1", "2", "90", "91"],
                    "H20": ["1", "2", "90", "91"],
                    "NMHC": ["1", "2", "11", "12", "13", "18", "19", "90", "91"],
                    "NOX": ["1", "2", "15", "16", "17", "90", "91"],
                    "PM10": ["1", "2", "15", "16", "17", "90", "91"],
                    "PM25": ["1", "2", "15", "16", "17", "90", "91"],
                    "Spar": ["1", "2", "90", "91"],
                    "SO2": ["1", "2", "15", "16", "17", "90", "91"],
                    "TEC": ["1", "2", "90", "91"],
                    "THC": ["1", "2", "11", "12", "13", "18", "19", "90", "91"],
                    "VOC": ["1", "2", "11", "12", "13", "15", "16", "17", "18", "19", "90", "91"]}

        # XML for pollutant process associations
        # create element for pollutant process associations
        polproc = etree.Element("pollutantprocessassociations")

        # populate subelements for pollutant processes
        # loop through all pollutants
        for _pol in _polname:
            # loop through all processes associated with each pollutant
            for _proc in _prockey[_pol]:
                pollutant = etree.SubElement(polproc,
                                             "pollutantprocessassociation",
                                             pollutantkey=_polkey[_pol])
                pollutant.set("pollutantname", _polname[_pol])
                pollutant.set("processkey", _proc)
                pollutant.set("processname", _procname[_proc])

        # Create XML element tree for MOVES road types
        # dictionary for road types
        _roaddict = {"1": "Off-Network",
                     "2": "Rural Restricted Access",
                     "3": "Rural Unrestricted Access",
                     "4": "Urban Restricted Access",
                     "5": "Urban Unrestricted Access"}
        # XML for road types
        roadtypes = etree.Element("roadtypes", {"separateramps": "false"})
        for _roads in _roaddict:
            roadtype = etree.SubElement(roadtypes, "roadtype",
                                        roadtypeid=_roads)
            roadtype.set("roadtypename", _roaddict[_roads])
            roadtype.set("modelCombination", "M1")

        # Create XML element tree for extra database information (leave empty)
        inputdatabase = etree.Element("inputdatabase", servername="")
        inputdatabase.set("databasename", "")
        inputdatabase.set("description", "")

        # Create full element tree for MOVES import file
        _runspecfilestring = (
            E.runspec(
                    description,
                    E.models(
                            etree.Element("model", value="ONROAD")
                    ),
                    etree.Element("modelscale", value="Rates"),
                    etree.Element("modeldomain", value="SINGLE"),
                    E.geographicselections(
                            geoselect
                    ),
                    timespan,
                    E.onroadvehicleselections(
                            vehicle_selection
                    ),
                    E.offroadvehicleselections(""
                                               ),
                    E.offroadvehiclesccs(""
                                         ),
                    roadtypes,
                    polproc,
                    E.databaseselections(""
                                         ),
                    E.internalcontrolstrategies(internalcontrol),
                    inputdatabase,
                    uncertaintyparam,
                    etree.Element("geographicoutputdetail",
                                  description="LINK"),
                    outputemissions,
                    outputdatabase,
                    etree.Element("outputtimestep", value="Hour"),
                    etree.Element("outputvmtdata", value="true"),
                    etree.Element("outputsho", value="false"),
                    etree.Element("outputsh", value="false"),
                    etree.Element("outputshp", value="false"),
                    etree.Element("outputshidling", value="true"),
                    etree.Element("outputstarts", value="true"),
                    etree.Element("outputpopulation", value="true"),
                    inputdatabase,
                    etree.Element("pmsize", value="0"),
                    outputfactors,
                    E.savedata(""
                               ),
                    E.donotexecute(""
                                   ),
                    gendata,
                    etree.SubElement(gendata, "donotperformfinalaggregation",
                                     selected="false"),
                    lookupflag,
                    # @TODO check that this works
                    version=self.moves_version)
        )

        # Transform element tree to string and save to file

        # create string from element tree
        _stringout = etree.tostring(_runspecfilestring, pretty_print=True,
                                    encoding='utf8')

        # create filename for runspec file using FIPS and scenario year
        _runspec_filename = os.path.join(self.save_path_runspecfiles,
                                         '{fips}_runspec_{year}.mrs'.format(
                                                 fips=fips, year=self.year))

        # save string to file
        fileout = open(_runspec_filename, "w")
        fileout.write(_stringout)
        fileout.close()

    def create_batch_files(self, fips):
        """
        Create and save batch files for running MOVES
        :return: None
        """

        # initialize kvals dictionary for string formatting
        kvals = dict()
        # scenario year
        kvals['year'] = self.year
        # scenario name
        kvals['title'] = self.model_run_title
        # timestamp of run
        kvals['timestamp'] = time.strftime('_%b-%d-%Y_%H%M', time.localtime())
        # FIPS code
        kvals['fips'] = fips

        # @TODO: change filepath so these don't write to the MOVES root
        # folder (should go to the scenario or project folder)

        # path for batch import file
        self.batchimport_filename = os.path.join(self.moves_path,
                                                 'batch_import_FPEAM_{fips}_{year}_{'
                                                 'title}_{timestamp}.bat'.format(
                                                         **kvals))
        # path for XML import files
        self.xmlimport_filename = os.path.join(self.save_path_importfiles,
                                               '{fips}_import_{year}.mrs'.format(
                                                       **kvals))
        # path for batch run file
        self.batchrun_filename = os.path.join(self.moves_path,
                                              'batch_run_FPEAM_{fips}_{year}_{title}_{'
                                              'timestamp}.bat'.format(**kvals))
        # path for XML runspec files
        self.runspec_filename = os.path.join(self.save_path_runspecfiles,
                                             '{fips}_runspec_{year}.mrs'.format(
                                                     **kvals))

        # Create batch file for importing data using MOVES County Data Manager

        # append import files to batch import file
        # @TODO: remove this echo and make a logger call
        with open(self.batchimport_filename, 'a') as csvfile:
            batchwriter = csv.writer(csvfile)
            batchwriter.writerow([self.setenv_file])
            batchwriter.writerow(['echo Running %s' % (os.path.join(
                    self.save_path_importfiles,
                    '{fips}_import_{year}.mrs'.format(fips=fips,
                                                      year=self.year)))])
            batchwriter.writerow([
                'java -Xmx512M gov.epa.otaq.moves.master.commandline.MOVESCommandLine'
                ' -i {importfile}'.format(
                        importfile=self.xmlimport_filename)])

        # Create batch file for running MOVES

        # append import files to batch run file
        with open(self.batchrun_filename, 'a') as csvfile:
            batchwriter = csv.writer(csvfile)
            batchwriter.writerow([self.setenv_file])
            # @TODO: remove this echo and make a logger call
            batchwriter.writerow(['echo Running %s' % (os.path.join(
                    self.save_path_runspecfiles,
                    '{fips}_runspec_{year}.mrs'.format(fips=fips,
                                                       year=self.year)))])
            batchwriter.writerow(['java -Xmx512M '
                                  'gov.epa.otaq.moves.master.'
                                  'commandline.MOVESCommandLine'
                                  ' -r {runspecfile}'.format(runspecfile=self.runspec_filename)])

    def get_cached_results(self):
        """

        :return: list of fips for which MOVES results already exist
        """

        # initialize kvals dict for SQL statement formatting
        kvals = dict()
        kvals['moves_output_db'] = self.moves_output_db
        kvals['year'] = self.year
        kvals['month'] = self.mo
        kvals['day'] = self.d

        _results_fips_sql = """SELECT MOVESScenarioID,
                                                      dist_table.MOVESRunID,
                                                      yearID,
                                                      monthID,
                                                      dayID,
                                                      hourID,
                                                      pollutantID,
                                                      processID,
                                                      fuelTypeID,
                                                      modelYearID,
                                                      roadTypeID,
                                                      avgSpeedBinID,
                                                      ratePerDistance,
                                                      state,
                                                      dist_table.fips
              FROM {moves_output_db}.rateperdistance AS dist_table
                INNER JOIN (SELECT distinct dist.fips, MOVESRunID
                            FROM {moves_output_db}.rateperdistance dist
                      INNER JOIN (SELECT fips, MAX(MOVESRunID) AS max_id
                                  FROM {moves_output_db}.rateperdistance
                                  GROUP BY fips) q
                              ON dist.MOVESRunID = q.max_id
                                  AND dist.fips = q.fips) runid_filter
                    ON dist_table.MOVESRunID =
                    runid_filter.MOVESRunID
              WHERE dist_table.yearID = {year} AND dist_table.monthID = {
              month} AND dist_table.dayID = {day};""".format(**kvals)

        # read in the table and get the list of unique fips for which
        # results already exist (takes year, month, day into account)
        _fips_cached = pd.read_sql(_results_fips_sql,
                                   self.moves_con).fips.unique()

        return _fips_cached

    def postprocess(self):
        """
        pulls moves output from database
        user input y/n: clear out old moves results
        postprocesses local copy to get rate per vehicle-mile by FIPS (saves
        this locally) and sends to routing for total emissions calculation
        :return: None
        """

        LOGGER.info('Retrieving MOVES output')

        # list of MOVES output tables that are currently used for
        # transportation
        _moves_table_list = ['ratePerDistance', 'ratePerVehicle']

        # initialize kvals dict for SQL statement formatting
        kvals = dict()
        kvals['moves_database'] = self.moves_database
        kvals['moves_output_db'] = self.moves_output_db
        kvals['source_type_id'] = self.source_type_id
        kvals['year'] = self.year
        kvals['month'] = self.mo
        kvals['day'] = self.d

        # some minor changes to the SQL tables in _moves_table_list
        # @TODO are these the tables that are continually added on to with
        # repeated MOVES runs, and if so can this postprocessing step be
        # revised and maybe made shorter?
        for _table in _moves_table_list:
            LOGGER.debug('Adding fips column to {t}'.format(t=_table))
            _add_fips_sql = """ALTER TABLE {moves_output_db}.{t} 
                                ADD COLUMN fips char(5);""".format(t=_table,
                                                                   **kvals)
            _nrows_fips_alter = self.moves_cursor.execute(_add_fips_sql)

            LOGGER.debug('Updating fips column to {t}'.format(t=_table))
            _update_fips_sql = """UPDATE {moves_output_db}.{t} 
                    SET fips = LEFT(MOVESScenarioID, 5);""".format(t=_table,
                                                                   **kvals)
            _nrows_fips_update = self.moves_cursor.execute(_update_fips_sql)

        # close cursor
        self.moves_cursor.close()

        # pull in rows from the ratePerDistance table, subsetting to grab
        # only the most recent runs for each FIPS in the table
        # @NOTE it would be better to filter on moves_run_list before
        # reading in because this statement takes a while, but then the
        # moves_run_list would need to be in the database
        # @NOTE if MOVES is run for more than one vehicle then this
        # calculation will need to be updated with sourceTypeID, regClassID
        # and SCC (or some subset of the three) being pulled in here as well
        #  as the rest of the columns
        _rateperdistance_table_sql = """SELECT MOVESScenarioID,
                                                      dist_table.MOVESRunID,
                                                      yearID,
                                                      monthID,
                                                      dayID,
                                                      hourID,
                                                      pollutantID,
                                                      processID,
                                                      fuelTypeID,
                                                      modelYearID,
                                                      roadTypeID,
                                                      avgSpeedBinID,
                                                      ratePerDistance,
                                                      state,
                                                      dist_table.fips
              FROM {moves_output_db}.rateperdistance AS dist_table
                INNER JOIN (SELECT distinct dist.fips, MOVESRunID
                            FROM {moves_output_db}.rateperdistance dist
                      INNER JOIN (SELECT fips, MAX(MOVESRunID) AS max_id
                                  FROM {moves_output_db}.rateperdistance
                                  GROUP BY fips) q
                              ON dist.MOVESRunID = q.max_id
                                  AND dist.fips = q.fips) runid_filter
                    ON dist_table.MOVESRunID =
                    runid_filter.MOVESRunID
              WHERE dist_table.yearID = {year} AND dist_table.monthID = {
              month} AND dist_table.dayID = {day};""".format(
                **kvals)

        # read in all possibly relevant entries from the rate per distance
        # table
        _rateperdistance_all = pd.read_sql(_rateperdistance_table_sql,
                                           self.moves_con)

        # create a filter for relevant rateperdistance rows based on which
        # fips in rateperdistance are equal to fips in the moves run list
        _rateperdistance_filter = _rateperdistance_all.fips.isin(
                self.moves_run_list.fips)

        # filter down the large rateperdistance table into just the rows
        # that are relevant to this run
        _rateperdistance = _rateperdistance_all[_rateperdistance_filter]

        # pull in rows from the ratePerVehicle table, subsetting to grab
        # only the most recent runs for each FIPS in the able
        # @NOTE if run for more than one vehicle then this statement will
        # need to include sourceTypeID, regClassID and/or SCC
        _ratepervehicle_table_sql = """SELECT MOVESScenarioID,
                                                veh_table.MOVESRunID,
                                                yearID,
                                                monthID,
                                                dayID,
                                                hourID,
                                                pollutantID,
                                                processID,
                                                fuelTypeID,
                                                modelYearID,
                                                ratePerVehicle,
                                                veh_table.fips
        FROM  moves_output_db.ratepervehicle AS veh_table
            INNER JOIN (SELECT distinct veh.fips, MOVESRunID
                        FROM moves_output_db.ratepervehicle veh
            INNER JOIN (SELECT fips, MAX(MOVESRunID) AS max_id
                        FROM moves_output_db.ratepervehicle
                        GROUP BY fips) q
                    ON veh.MOVESRunID = q.max_id
                        AND veh.fips = q.fips) runid_filter
                ON veh_table.MOVESRunID = runid_filter.MOVESRunID
              WHERE dist_table.yearID = {year} AND dist_table.monthID = {
              month} AND dist_table.dayID = {day};""".format(
                **kvals)

        _ratepervehicle_all = pd.read_sql(_ratepervehicle_table_sql,
                                          self.moves_con)

        _ratepervehicle_filter = _ratepervehicle_all.fips.isin(
                self.moves_run_list.fips)

        _ratepervehicle = _ratepervehicle_all[_ratepervehicle_filter]

        LOGGER.debut('Postprocessing MOVES output')

        # add state column to both tables by pulling out first two digits of
        #  MOVESScenarioID
        _rateperdistance['state'] = \
            _rateperdistance.MOVESScenarioID.str.slice(stop=2)
        _ratepervehicle['state'] = \
            _ratepervehicle.MOVESScenarioID.str.slice(stop=2)

        # create the average speed table that will be used in calculating
        # the average emissions rate per distance
        # the average speed table is a join of the avgspeddistribution and
        # hourday tables, both in the MOVES default database
        _averagespeed_query = """SELECT table1.roadTypeID,
                                        table1.avgSpeedBinID,
                                        table1.avgSpeedFraction,
                                        table2.hourID,
                                        table2.dayID
                   FROM {moves_database}.avgspeeddistribution table1
                   LEFT JOIN {moves_database}.hourday table2
                   ON table1.hourDayID = table2.hourDayID
                   WHERE sourceTypeID = {source_type_id};""".format(**kvals)

        # pull the average speed table in from the database and merge with
        # the VMT fraction table created during MOVES setup
        # @NOTE the roadTypeID column in roadtypevmt needs to be int64 type
        _averagespeed = pd.read_sql(_averagespeed_query,
                                    self.moves_con).merge(self.roadtypevmt,
                                                          on='roadTypeID')

        # Calculate total running emissions per trip (by pollutant)
        # Equal to sum(ratePerDistance * vmtfrac_in_speedbin[i] * vmt)
        # for all speed bins, pollutant processes, day types, hours,
        # and road types
        _join_dist_avgspd = _rateperdistance.merge(_averagespeed,
                                                   on=('roadTypeID',
                                                       'avgSpeedBinID',
                                                       'dayID',
                                                       'hourID'))

        # calculate non-summed rate per distance and do a groupby to prepare
        #  for summing rates per distance over pollutant processes, hours,
        # speed bins, and road types to get one rate per
        # fips-month-day-pollutant combo
        _join_dist_avgspd.eval('averageRatePerDistance = ratePerDistance * '
                               'avgSpeedFraction * '
                               'vmt_fraction', inplace=True).groupby(['fips',
                                                                      'state',
                                                                      'yearID',
                                                                      'monthID',
                                                                      'dayID',
                                                                      'pollutantID'],
                                                                     as_index=False)

        # calculate final pollutant rates per distance
        _avgRateDist = _join_dist_avgspd.sum()[['fips', 'state', 'monthID',
                                                'dayID', 'pollutantID',
                                                'averageRatePerDistance']]

        # merge the truck capacity numbers with the rate per distance merge
        # to prep for calculating number of trips
        _run_emissions = _avgRateDist.merge(self.prod_moves_runs, how='left',
                                            left_on=['fips', 'state'],
                                            right_on=['MOVES_run_fips',
                                                      'MOVES_state']).merge(
                self.truck_capacity[['feedstock',
                                     'truck_capacity']],
                how='left',
                on='feedstock')

        # @TODO insert routing output in here
        _run_emissions['vmt'] = 1.0

        # evaluate running emissions
        _run_emissions.eval(
                'pollutant_amount = averageRatePerDistance * vmt * '
                'feedstock_amount / truck_capacity',
                inplace=True)

        # start and hotelling emissions

        _avgRateVeh = _ratepervehicle.groupby(['fips', 'state', 'yearID',
                                               'monthID', 'dayID',
                                               'pollutantID'],
                                              as_index=False).sum(
                inplace=True)[['fips', 'state', 'yearID', 'monthID', 'dayID',
                               'pollutantID', 'ratePerVehicle']]

        # merge raw moves output with production data and truck capacities
        _start_hotel_emissions = _avgRateVeh.merge(self.prod_moves_runs,
                                                   how='left',
                                                   left_on=['fips', 'state'],
                                                   right_on=['MOVES_run_fips',
                                                             'MOVES_state']).merge(
                self.truck_capacity[['feedstock', 'truck_capacity']],
                how='left',
                on='feedstock')

        # calculate start and hotelling emissions
        _start_hotel_emissions.eval('pollutant_amount = ratePerVehicle * '
                                    'feedstock_amount / truck_capacity',
                                    inplace=True)

        # append the run emissions with the start and hotelling emissions
        _transportation_emissions = _run_emissions[['region_production',
                                                    'state', 'year',
                                                    'tillage_type',
                                                    'feedstock',
                                                    'pollutantID',
                                                    'pollutant_amount']].append(
                _start_hotel_emissions[['region_production', 'state', 'year',
                                        'tillage_type', 'feedstock', 'pollutantID',
                                        'pollutant_amount']],
                ignore_index=True)

        # @TODO convert pollutant amount from grams to ??

        # sum up by pollutant type for semi-final module output
        _transportation_emissions = _transportation_emissions.groupby(
                ['region_production', 'state', 'year', 'tillage_type', 'feedstock',
                 'pollutantID'], as_index=False).sum()

        return _transportation_emissions

    def run(self):
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
        # this gets saved in self for use in postprocessing
        _prod_by_fips_feed = _prod_merge.groupby(['MOVES_fips',
                                                  'MOVES_state',
                                                  'feedstock'],
                                                 as_index=False).sum()

        # within each FIPS-year-feedstock combo, find the highest
        # feedstock production
        _max_amts_feed = _prod_by_fips_feed.groupby(['MOVES_state',
                                                     'feedstock'],
                                                    as_index=False).max()

        if self.moves_state_level:

            # sum total feedstock production within each fips-state-year combo
            _amts_by_fips = _prod_by_fips_feed.groupby(['MOVES_fips',
                                                        'MOVES_state'],
                                                       as_index=False).sum()

            # locate the fips within each state with the highest total
            # feedstock production
            _max_amts = _amts_by_fips.groupby(['MOVES_state'],
                                              as_index=False).max()

            # strip out duplicates (shouldn't be any) to create a list of
            # unique fips-state combos to run MOVES on
            self.moves_run_list = _max_amts[['MOVES_fips',
                                             'MOVES_state']].drop_duplicates()

        elif self.moves_by_feedstock:

            # get a list of unique fips-state-year combos to run MOVES on
            # keep feedstock in there to match results from each MOVES run
            # to the correct set of feedstock production data
            self.moves_run_list = _max_amts_feed[['MOVES_fips',
                                                  'MOVES_state',
                                                  'feedstock']].drop_duplicates()

        else:

            # if neither moves_state_level nor moves_by_feedstock are True,
            # the fips-state-year combos to run MOVES on come straight from
            # the production data
            self.moves_run_list = _prod_merge[['MOVES_fips',
                                               'MOVES_state']].drop_duplicates()

        # rename the fips and state columns for easier merging with the
        # production df
        self.moves_run_list.rename(index=str,
                                   columns={'MOVES_fips': 'MOVES_run_fips',
                                            'MOVES_state': 'MOVES_run_state'},
                                   inplace=True)

        # merge production with moves run fips and states and save in self
        # for use in postprocessing
        self.prod_moves_runs = _prod_merge.merge(self.moves_run_list,
                                                 left_on=('MOVES_state',),
                                                 right_on=(
                                                     'MOVES_run_state'))[
            ['MOVES_fips',
             'MOVES_run_fips',
             'MOVES_state',
             'region_production',
             'region_destination',
             'tillage_type',
             'year_y',
             'feedstock',
             'feedstock_measure',
             'feedstock_amount']].drop_duplicates()

        # rename the non-summed year column to maintain that identifier
        self.prod_moves_runs.rename(index=str, columns={'year_y': 'year'},
                                    inplace=True)

        # @NOTE prod_moves_runs is being stored in self as a potential
        # output or check on functionality; it'll also be used in
        # postprocessing

        # after generating the list of FIPS over which MOVES is run,
        # begin to create the input data and run MOVES

        if self.use_cached_results:

            # run only fips for which there are no cached results
            # @TODO implement: subset and redefine moves_run_list, 
            # excluding those fips for which results already exist

            _exclude_fips = self.get_cached_results()

            for _fips in _exclude_fips:
                # report that MOVES run already complete
                LOGGER.info('MOVES run already complete for fips: %s' %
                            _fips)

            # create shortened list of fips to run through MOVES
            _run_fips = [x for x in self.prod_moves_runs.MOVES_run_fips
                         if x not in _exclude_fips]

        else:

            # run all fips regardless of whether cached results exist or not
            _run_fips = self.moves_run_list.MOVES_run_fips

        # only go through the setup and run steps if there are fips that
        # need to be run
        if _run_fips.__len__() > 0:
            # create national datasets only once per FPEAM
            self.create_national_data()

            # loop thru rows of moves_run_list to generate input data files
            # for each FIPS
            for _fips in _run_fips:
                # create county-level data files
                self.create_county_data(fips=_fips)

                # create XML import files
                self.create_xml_import(fips=_fips)

                # create XML run spec files
                self.create_xml_runspec(fips=_fips)

                # create batch files for importing and running MOVES
                self.create_batch_files(fips=_fips)
                batch_run_dict = None

                # actually send the commands to import files into MOVES and
                # then run MOVES

                # import MOVES data into datbase
                LOGGER.debug('Importing MOVES files')

                # execute batch file and log output
                command = 'cd {moves_path} & setenv.bat & ' \
                          'java -Xmx512M ' \
                          'gov.epa.otaq.moves.master.commandline.MOVESCommandLine -i {import_file}' \
                          ''.format(moves_path=self.moves_path,
                                    import_file=self.xmlimport_filename)

                os.system(command)

                # execute batch file and log output
                LOGGER.info('Running MOVES for fips: %s' % _fips)
                LOGGER.info('Batch file MOVES for importing data: %s' % (
                    self.batchimport_filename,))

                command = 'cd {moves_folder} & setenv.bat & ' \
                          'java -Xmx512M ' \
                          'gov.epa.otaq.moves.master.commandline.MOVESCommandLine' \
                          '-r {run_moves}'.format(
                           moves_folder=self.moves_path,
                           run_moves=batch_run_dict[_fips])  # @TODO what's this
                os.system(command)

                # @TODO this is a stopgap way to record which MOVES runs
                # have been completed - replace with proper caching method
                self.completed_moves_runs.append("{fips}_{year}".format(
                        fips=_fips, year=self.year))

        # postprocess output - same regardless of cached status
        self.postprocess()

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        # close connection to MOVES database
        self.moves_con.close()

        # process exceptions
        if exc_type is not None:
            LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self
