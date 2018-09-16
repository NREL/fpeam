import os

import numpy as np
import pandas as pd
import pymysql
from lxml import etree
from lxml.builder import E

from FPEAM import utils
from .Module import Module
from ..Data import (RegionFipsMap, TruckCapacity, TransportationGraph, CountyNode)
from ..Router import Router

LOGGER = utils.logger(name=__name__)

# @TODO keep the movesscenarioID in output table to identify cached results
# @TODO separate directories for separate scenario names, also tack on
# scenario name to MOVES input file names


class MOVES(Module):

    def __init__(self, config, production, equipment=None):
        """

        :param config: [ConfigObj]
        :param production: [DataFrame]
        :param equipment: [DataFrame]
        """

        # init parent
        super(MOVES, self).__init__(config=config)

        self.production = production
        self.equipment = equipment

        # create a dictionary of conversion factors for later use
        self.conversion_factors = self._set_conversions()

        self._router = None

        _transportation_graph = TransportationGraph(fpath=self.config['transportation_graph'])
        _county_nodes = CountyNode(fpath=self.config['county_nodes'])

        if not _transportation_graph.empty or not _county_nodes.empty:
            LOGGER.info('Loading routing data; this may take a few minutes')
            self.router = Router(edges=_transportation_graph, node_map=_county_nodes)  # @TODO: takes ages to load

        self.year = self.config['year']
        self.region_fips_map = RegionFipsMap(fpath=self.config['region_fips_map'])
        self.feedstock_measure_type = self.config.get('feedstock_measure_type')

        # this is a DF read in from a csv file
        self.truck_capacity = TruckCapacity(fpath=self.config['truck_capacity'])

        self.use_cached_results = self.config.get('use_cached_results')

        # scenario name
        self.model_run_title = self.config.get('scenario_name')

        # MOVES input and output databases - set names
        self.moves_database = self.config.get('moves_database')
        self.moves_output_db = self.config.get('moves_output_db')

        # open connection to MOVES default database for input/output
        self._conn = pymysql.connect(host=self.config.get('moves_db_host'),
                                     user=self.config.get('moves_db_user'),
                                     password=self.config.get('moves_db_pass'),
                                     db=self.config.get('moves_database'),
                                     local_infile=True)

        # get version of MOVES for XML trees
        self.moves_version = self.config.get('moves_version')

        # input and output file directories - get paths from config
        self.moves_path = self.config.get('moves_path')
        self.moves_datafiles_path = self.config.get('moves_datafiles_path')

        # file-specific input directories - combine paths from config with
        # file-specific subdirectory names
        self.save_path_importfiles = os.path.join(self.moves_datafiles_path, 'import_files')
        self.save_path_runspecfiles = os.path.join(self.moves_datafiles_path, 'run_specs')
        self.save_path_countyinputs = os.path.join(self.moves_datafiles_path, 'county_inputs')
        self.save_path_nationalinputs = os.path.join(self.moves_datafiles_path, 'national_inputs')

        # store avft dataframe in self for later saving
        self.avft = pd.read_csv(self.config.get('avft'), header=0)

        # additional input file paths
        self.avft_filename = os.path.join(self.save_path_nationalinputs, 'avft.csv')
        self.setenv_file = os.path.join(self.moves_path, 'setenv.bat')

        # file-specific output directory - combine paths from config with
        # file-specific subdirectory names
        self.save_path_outputs = os.path.join(self.moves_datafiles_path, 'outputs')

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

        # user input - timespan for which MOVES is run
        self.moves_timespan = self.config.get('moves_timespan')

        # parameters for generating XML runspec files for MOVES
        self.month = self.moves_timespan['month']
        self.day = self.moves_timespan['day']
        self.beginning_hour = self.moves_timespan['beginning_hour']
        self.ending_hour = self.moves_timespan['ending_hour']

        # machine where MOVES output db lives
        self.db_host = self.config.get('moves_db_host')

        # user input - get toggle for running moves by state-level fips
        # finds FIPS with highest total (summed across feedstocks)
        # production in each state, runs MOVES only for those FIPS (50 FIPS)
        self.moves_by_state = self.config.get('moves_by_state')

        # user input - get toggle for running moves by feedstock and state
        # finds FIPS with highest production by feedstock in each state,
        # runs MOVES only
        # for those FIPS (50 x nfeedstock FIPS)
        self.moves_by_state_and_feedstock = self.config.get('moves_by_state_and_feedstock')

        # user input - default values used for running MOVES, actual VMT
        #  used to compute total emission in postprocessing
        self.vmt_short_haul = self.config.as_int('vmt_short_haul')

        # user input - population of combination short-haul trucks (assume one
        # per trip and only run MOVES for single trip)
        self.pop_short_haul = self.config.as_int('pop_short_haul')

        # user input - type of vehicle used to transport biomass
        self.hpmsv_type_id = self.config.get('hpmsv_type_id')

        # user input - subtype of vehicle used to transport biomass
        self.source_type_id = self.config.get('source_type_id')

        # selection of fuels to run
        # 20 is conventional diesel and 21 is biodiesel
        # @NOTE possibly add to GUI as user input in the future
        # can select additional fuel subtypes in list form
        self.fuel_subtype_id = (20, 21)

        # selection of fuel supply type
        # not sure what this means
        # @NOTE possibly add to GUI as user input in the future
        self.fuel_supply_fuel_type_id = '2'

        # user input - fraction of VMT on each road type (dictionary type)
        self._vmt_fraction = None
        self.vmt_fraction = self.config.get('vmt_fraction')

        # polname, polkey, procname, prockey and roaddict are used in
        # generating the XML import and runspec files for MOVES

        # @todo polname, polkey, procname, prockey and pollutant_name could be
        # converted to user inputs to allow for more or fewer pollutant
        # calculations dictionary of pollutant shorthand to MOVES name
        self.polname = {"NH3": "Ammonia (NH3)",
                        "CO": "Carbon Monoxide (CO)",
                        "NOX": "Oxides of Nitrogen",
                        "PM10": "Primary Exhaust PM10  - Total",
                        "PM25": "Primary Exhaust PM2.5 - Total",
                        "SO2": "Sulfur Dioxide (SO2)",
                        "VOC": "Volatile Organic Compounds"}

        # dictionary of pollutant shorthand to MOVES pollutantid
        self.polkey = {"NH3": "30",
                       "CO": "2",
                       "NOX": "3",
                       "PM10": "100",
                       "PM25": "110",
                       "SO2": "31",
                       "VOC": "87"}

        # dictionary of MOVES pollutant process numbers to MOVES pollutant
        # process descriptions
        self.procname = {"1": "Running Exhaust",
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
        self.prockey = {"NH3": ["1", "2", "15", "16", "17", "90", "91"],
                        "CO": ["1", "2", "15", "16", "17", "90", "91"],
                        "NOX": ["1", "2", "15", "16", "17", "90", "91"],
                        "PM10": ["1", "2", "15", "16", "17", "90", "91"],
                        "PM25": ["1", "2", "15", "16", "17", "90", "91"],
                        "SO2": ["1", "2", "15", "16", "17", "90", "91"],
                        "VOC": ["1", "2", "11", "12", "13", "15", "16", "17", "18", "19", "90", "91"]}

        # dictionary for road types
        self.roaddict = {"1": "Off-Network",
                         "2": "Rural Restricted Access",
                         "3": "Rural Unrestricted Access",
                         "4": "Urban Restricted Access",
                         "5": "Urban Unrestricted Access"}

        # create data frame for renaming pollutants during postprocessing
        self.pollutant_names = pd.DataFrame({'pollutant': ['NH3', 'CO',
                                                           'NOX',
                                                           'PM10', 'PM25',
                                                           'SO2', 'VOC'],
                                             'pollutantID': [30, 2, 3,
                                                             100, 110,
                                                             31, 87]})

    @property
    def router(self):
        return self._router

    @router.setter
    def router(self, value):
        try:
            getattr(value, 'get_route')
        except AttributeError:
            LOGGER.error('%s is not a valid routing engine. '
                         'Method .get_route(FIPS, FIPS) is required' % value)
        else:
            self._router = value

    @property
    def vmt_fraction(self):
        return self._vmt_fraction

    @vmt_fraction.setter
    def vmt_fraction(self, value):

        # verify complete distribution
        try:
            assert sum(value.values()) == 1
        except AssertionError:
            raise ValueError('vmt_fraction must sum to 1.0')
        else:
            self._vmt_fraction = value

    def _create_national_data(self):
        """
        Create national data for MOVES, including:
            average speed distribution
            age distribution
            day VMT fraction
            month VMT fraction
            hour VMT fraction
            road type fraction

        Saves user-created Alternate Vehicle Fuels & Technologies (avft)
        file in correct directory

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
                     sourceTypeID = {source_type_id};""".format(**kvals)

            # pull data from database and save in a csv
            pd.read_sql(_table_sql, self._conn).to_csv(os.path.join(
                    self.save_path_nationalinputs, '%s.csv' % (kvals['table'],)),
                    index=False)

        # save alternative vehicle fuels and technology (avft) file to
        # national input file directory
        self.avft.to_csv(self.avft_filename, sep=',', index=False)

        # default age distribution file creation
        # age distribution for user-specified source_type_id and year is pulled
        #  in from the MOVES database and written to file
        kvals['year'] = self.year

        _agedist_sql = """SELECT * FROM
        {moves_database}.sourcetypeagedistribution WHERE
        sourceTypeID = {source_type_id} AND yearID = {year};""".format(**kvals)

        # save this file name to self so it can be used by create_xml_import
        self.agedistfilename = os.path.join(
                self.save_path_nationalinputs,
                'default-age-distribution-tool-moves%s.csv' % (self.year,))

        # pull data from database and save in a csv
        pd.read_sql(_agedist_sql, self._conn).to_csv(self.agedistfilename, index=False)

        # construct dataframe of road type VMTs from config file input
        _vmt_fraction = {2: self.vmt_fraction['rural_restricted'],
                         3: self.vmt_fraction['rural_unrestricted'],
                         4: self.vmt_fraction['urban_restricted'],
                         5: self.vmt_fraction['urban_unrestricted']}

        self.roadtypevmt = pd.DataFrame.from_dict(_vmt_fraction,
                                                  orient='index',
                                                  columns=['roadTypeVMTFraction'])
        self.roadtypevmt['roadTypeID'] = self.roadtypevmt.index
        self.roadtypevmt['sourceTypeID'] = np.repeat(self.source_type_id, 4)

        # write roadtypevmt to csv
        self.roadtypevmt_filename = os.path.join(self.save_path_nationalinputs, 'roadtype.csv')
        self.roadtypevmt.to_csv(self.roadtypevmt_filename, sep=',', index=False)

    def _create_county_data(self, fips):
        """

        Create county-level data for MOVES, including:
            vehicle miles travelled
            source type population
            fuel supply type
            fuel formulation
            fuel usage fraction
            meteorology

        County-level input files for MOVES that vary by FIPS.

        :return:
        """

        LOGGER.debug('Creating county-level data files for MOVES')

        # set up kvals for SQL query formatting
        kvals = dict()
        kvals['fips'] = fips
        kvals['year'] = self.year
        kvals['moves_database'] = self.moves_database
        kvals['fuel_subtype_id'] = ', '.join([str(_) for _ in self.fuel_subtype_id])
        kvals['fuel_supply_fuel_type_id'] = self.fuel_supply_fuel_type_id
        kvals['countyID'] = str(int(fips))
        kvals['zoneID'] = str(int(fips)) + '0'

        # annual vehicle miles traveled by vehicle type
        # need one for each FIPS
        _vmt = pd.DataFrame({'HPMSVtypeID': self.hpmsv_type_id,
                             'yearID': self.year,
                             'HPMSBaseYearVMT': self.vmt_short_haul},
                            index=['0'])

        # this name is FIPS dependent, cannot be created in init
        self.vmt_filename = os.path.join(self.save_path_countyinputs,
                                         '{fips}_vehiclemiletraveled_{'
                                         'year}.csv'.format(**kvals))

        # write vehicle miles traveled to file
        _vmt.to_csv(self.vmt_filename, index=False)

        # source type population (number of vehicles by vehicle type)
        # need one for each fips
        _sourcetype = pd.DataFrame({'yearID': self.year,
                                    'sourceTypeID': self.source_type_id,
                                    'sourceTypePopulation':
                                        self.pop_short_haul},
                                   index=['0'])

        # this name is FIPS dependent, cannot be created in init
        self.sourcetype_filename = os.path.join(self.save_path_countyinputs,
                                                '{fips}_sourcetype_{'
                                                'year}.csv'.format(**kvals))

        # write source type population to file
        _sourcetype.to_csv(self.sourcetype_filename, index=False)

        # export county-level fuel supply data
        # need one for each FIPS
        _fuelsupply_sql = """SELECT * FROM {moves_database}.fuelsupply
                            WHERE {moves_database}.fuelsupply.fuelRegionID =
                            (SELECT DISTINCT regionID FROM {moves_database}.regioncounty 
                            WHERE countyID = '{countyID}' AND fuelYearID = '{year}')
                            AND {moves_database}.fuelsupply.fuelYearID = '{year}';""".format(**kvals)

        # save for later use in create_xml_imports
        self.fuelsupply_filename = os.path.join(self.save_path_countyinputs,
                                                '{fips}_fuelsupply_{year}.csv'.format(**kvals))

        # pull data from database and save in a csv
        pd.read_sql(_fuelsupply_sql, self._conn).to_csv(
            self.fuelsupply_filename, index=False)

        # export county-level fuel formulation data
        # need one for each FIPS-year combination
        _fuelform_sql = """SELECT * FROM {moves_database}.fuelformulation
                            WHERE {moves_database}.fuelformulation.fuelSubtypeID
                            IN ({fuel_subtype_id});""".format(**kvals)

        # this name is FIPS dependent, cannot be created in init
        self.fuelformulation_filename = os.path.join(
                self.save_path_countyinputs, '{fips}_fuelformulation_{'
                                             'year}.csv'.format(**kvals))

        # pull data from database and save in a csv
        pd.read_sql(_fuelform_sql,
                    self._conn).to_csv(self.fuelformulation_filename,
                                       index=False)

        # export county-level fuel usage fraction data
        # need one for each FIPS-year combination
        _fuelusagename_sql = """SELECT * FROM {moves_database}.fuelusagefraction
                            WHERE {moves_database}.fuelusagefraction.countyID =
                            '{countyID}' AND
                            {moves_database}.fuelusagefraction.fuelYearID =
                            '{year}' AND
                            {moves_database}.fuelusagefraction.fuelSupplyFuelTypeID =
                            {fuel_supply_fuel_type_id};""".format(**kvals)

        # this name is FIPS dependent, cannot be created in init
        self.fuelusage_filename = os.path.join(self.save_path_countyinputs,
                                               '{fips}_fuelusagefraction_{'
                                               'year}.csv'.format(**kvals))

        # pull data from database and save in a csv
        pd.read_sql(_fuelusagename_sql, self._conn).to_csv(
            self.fuelusage_filename, index=False)

        # export county-level meteorology data
        # need one for each FIPS
        _met_sql = """SELECT * FROM {moves_database}.zonemonthhour 
                      WHERE {moves_database}.zonemonthhour.zoneID = {zoneID}""".format(**kvals)

        # this name is FIPS dependent, cannot be created in init
        self.met_filename = os.path.join(self.save_path_countyinputs,
                                         '{fips}_met.csv'.format(**kvals))

        # pull data from database and save in a csv
        pd.read_sql(_met_sql, self._conn).to_csv(self.met_filename,
                                                 index=False)

    def _create_xml_import(self, fips):
        """

        Create and save XML import files for running MOVES

        :return: None
        """

        # assemble kvals dict for string & filepath formatting
        kvals = dict()
        kvals['fips'] = fips
        kvals['year'] = self.year

        # set parser to leave CDATA sections in document
        _parser = etree.XMLParser(strip_cdata=False, recover=True)

        # create these files here since they were generated in a loop in
        # create_national_inputs - no stored filename
        # path to average speed distribution file (national inputs)
        _avgspeeddist_filename = os.path.join(self.save_path_nationalinputs, 'avgspeeddistribution.csv')
        _month_vmt_filename = os.path.join(self.save_path_nationalinputs, 'monthvmtfraction.csv')
        _day_vmt_filename = os.path.join(self.save_path_nationalinputs, 'dayvmtfraction.csv')
        _hour_vmt_filename = os.path.join(self.save_path_nationalinputs, 'hourvmtfraction.csv')

        # create XML for elements with CDATA
        self.internalcontrol = etree.XML(
                '<internalcontrolstrategy classname="gov.epa.otaq.moves.master.implementation.'
                'ghg.internalcontrolstrategies.rateofprogress.RateOfProgressStrategy">'
                '<![CDATA[useParameters	No]]></internalcontrolstrategy>',
                _parser)
        self.agename = "<filename>{agedistfilename}</filename>".format(
                agedistfilename=self.agedistfilename)
        self.agefile = etree.XML(self.agename, _parser)
        self.speedfile = etree.XML(
                "<filename>{speedfilename}</filename>".format(
                        speedfilename=_avgspeeddist_filename), _parser)
        self.fuelsupfile = etree.XML(
                "<filename>{fuelsupfilename}</filename>".format(
                        fuelsupfilename=self.fuelsupply_filename), _parser)
        self.fuelformfile = etree.XML(
                "<filename>{fuelformfilename}</filename>".format(
                        fuelformfilename=self.fuelformulation_filename), _parser)
        self.fuelusagefile = etree.XML(
                "<filename>{fuelusagefilename}</filename>".format(
                        fuelusagefilename=self.fuelusage_filename), _parser)
        self.avftfile = etree.XML("<filename>{avftfilename}</filename>".format(
                avftfilename=self.avft_filename), _parser)
        self.metfile = etree.XML("<filename>{metfilename}</filename>".format(
                metfilename=self.met_filename), _parser)
        self.roadtypefile = etree.XML(
                "<filename>{roadtypefilename}</filename>".format(
                        roadtypefilename=self.roadtypevmt_filename), _parser)
        self.sourcetypefile = etree.XML(
                "<filename>{sourcetypefilename}</filename>".format(
                        sourcetypefilename=self.sourcetype_filename), _parser)
        self.HPMSyearfile = etree.XML(
                "<filename>{vmtfilename}</filename>".format(
                        vmtfilename=self.vmt_filename), _parser)
        self.monthVMTfile = etree.XML(
                "<filename>{monthvmtfilename}</filename>".format(
                        monthvmtfilename=_month_vmt_filename), _parser)
        self.dayVMTfile = etree.XML(
                "<filename>{dayvmtfilename}</filename>".format(
                        dayvmtfilename=_day_vmt_filename), _parser)
        self.hourVMTfile = etree.XML(
                "<filename>{hourvmtfilename}</filename>".format(
                        hourvmtfilename=_hour_vmt_filename), _parser)

        # input database
        self.db_in = "fips_{fips}_{year}_in".format(fips=fips, year=self.year)
        # scenario ID for MOVES runs
        # ends up in tables in the MOVES output database
        self.scenid = "{fips}_{year}_{month}_{day}".format(fips=fips,
                                                           day=self.day,
                                                           month=self.month,
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
        etree.SubElement(timespan, "year", key=self.year.__str__())

        # set month
        etree.SubElement(timespan, "month", id=self.month.__str__())

        # loop through days (2 = weekend; 5 = weekday)
        etree.SubElement(timespan, "day", id=self.day.__str__())

        # loop through start hours
        etree.SubElement(timespan, "beginhour", id=self.beginning_hour.__str__())

        # loop through end hours
        etree.SubElement(timespan, "endhour", id=self.ending_hour.__str__())

        # aggregate at hourly level
        etree.SubElement(timespan, "aggregateBy", key="Hour")

        # Create XML element tree for MOVES vehicle type
        # @NOTE Currently only for combination short-haul truck

        # XML for vehicle type selections
        # combination short-haul truck
        # @TODO convert all of these to user inputs pulled from config
        vehicle_selection = etree.Element("onroadvehicleselection",
                                          fueltypeid=self.fuel_supply_fuel_type_id.__str__())
        vehicle_selection.set("fueltypedesc", "Diesel Fuel")
        vehicle_selection.set("sourcetypeid", self.source_type_id.__str__())
        vehicle_selection.set("sourcetypename", "Combination Short-haul Truck")

        # Create XML element tree for MOVES pollutant processes
        # Currently includes: CO, NH3, PM10, PM2.5, SO2, NOX, VOC,
        # and prerequisites

        # XML for pollutant process associations
        # create element for pollutant process associations
        polproc = etree.Element("pollutantprocessassociations")

        # populate subelements for pollutant processes
        # loop through all pollutants
        for _pol in self.polname:
            # loop through all processes associated with each pollutant
            for _proc in self.prockey[_pol]:
                pollutant = etree.SubElement(polproc,
                                             "pollutantprocessassociation",
                                             pollutantkey=self.polkey[_pol])
                pollutant.set("pollutantname", self.polname[_pol])
                pollutant.set("processkey", _proc)
                pollutant.set("processname", self.procname[_proc])

        # Create XML element tree for MOVES road types

        # XML for road types
        roadtypes = etree.Element("roadtypes", {"separateramps": "false"})
        for roads in self.roaddict:
            roadtype = etree.SubElement(roadtypes, "roadtype", roadtypeid=roads)
            roadtype.set("roadtypename", self.roaddict[roads])
            roadtype.set("modelCombination", "M1")

        # Create XML element tree for MOVES input database information

        # XML for database selection
        databasesel = etree.Element("databaseselection", servername=self.db_host)
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
                                              _parser),
                                    E.parts(E.sourceTypeAgeDistribution(self.agefile))),
                            E.avgspeeddistribution(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(E.avgSpeedDistribution(self.speedfile))),
                            E.fuel(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(
                                            E.FuelSupply(self.fuelsupfile),
                                            E.FuelFormulation(self.fuelformfile),
                                            E.FuelUsageFraction(self.fuelusagefile),
                                            E.AVFT(self.avftfile),
                                    )),
                            E.zoneMonthHour(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(E.zonemonthhour(self.metfile))),
                            E.rampfraction(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(E.roadType(E.filename("")))),
                            E.roadtypedistribution(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(E.roadTypeDistribution(self.roadtypefile))),
                            E.sourcetypepopulation(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(E.sourceTypeYear(self.sourcetypefile))),
                            E.starts(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
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
                                              _parser),
                                    E.parts(
                                            E.HPMSVtypeYear(self.HPMSyearfile),
                                            E.monthVMTFraction(self.monthVMTfile),
                                            E.dayVMTFraction(self.dayVMTfile),
                                            E.hourVMTFraction(self.hourVMTfile),
                                    )),
                            E.hotelling(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(
                                            E.hotellingActivityDistribution(E.filename("")),
                                            E.hotellingHours(E.filename("")))),
                            E.imcoverage(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(E.IMCoverage(E.filename("")))),
                            E.onroadretrofit(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(E.onRoadRetrofit(E.filename("")))),
                            E.generic(
                                    etree.XML('<description><![CDATA[]]></description>',
                                              _parser),
                                    E.parts(E.anytable(E.tablename("agecategory"),
                                                       E.filename("")))),
                            mode="county")
            )
        )

        # Transform element tree to string and save to file

        # create string from element tree
        stringout = etree.tostring(importfilestring, pretty_print=True,
                                   encoding='utf8')

        # create import filename using FIPS code, crop, and scenario year
        self.xmlimport_filename = os.path.join(self.save_path_importfiles,
                                    '{fips}_import_{year}.mrs'.format(
                                            fips=fips, year=self.year))

        # path for XML runspec files
        self.runspec_filename = os.path.join(self.save_path_runspecfiles,
                                             '{fips}_runspec_{year}.mrs'.format(
                                                 **kvals))

        # save string to file
        with open(self.xmlimport_filename, 'wb') as _fileout:
            _fileout.write(stringout)
            _fileout.close()

    def _create_xml_runspec(self, fips):
        """
        Create and save XML runspec files for running MOVES
        :return: None
        """

        # set parser to leave CDATA sections in document
        _parser = etree.XMLParser(strip_cdata=False)

        # scenario ID for MOVES runs
        _scenid = "{fips}_{year}_{month}_{day}".format(fips=fips,
                                                       day=self.day,
                                                       month=self.month,
                                                       year=self.year)

        # Create XML element tree for elements with MOVES inputs with CDATA
        description = etree.XML('<description><![CDATA[]]></description>', _parser)
        internalcontrol = etree.XML(
                '<internalcontrolstrategy classname="gov.epa.otaq.moves.master.implementation.ghg.'
                'internalcontrolstrategies.rateofprogress.RateOfProgressStrategy">'
                '<![CDATA[useParameters	No]]></internalcontrolstrategy>', _parser)

        # Create XML element tree for MOVES uncertainty parameters
        uncertaintyparam = etree.Element("uncertaintyparameters", uncertaintymodeenabled="false")
        uncertaintyparam.set("numberofrunspersimulation", "0")
        uncertaintyparam.set("numberofsimulations", "0")

        # Create XML element tree for MOVES output emissions breakdown,
        # which specifies which outputs are included in MOVES analysis
        outputemissions = etree.Element("outputemissionsbreakdownselection")
        etree.SubElement(outputemissions, "modelyear", selected="false")
        etree.SubElement(outputemissions, "fueltype", selected="false")
        etree.SubElement(outputemissions, "fuelsubtype", selected="false")
        etree.SubElement(outputemissions, "emissionprocess", selected="true")
        etree.SubElement(outputemissions, "onroadoffroad", selected="true")
        etree.SubElement(outputemissions, "roadtype", selected="true")
        etree.SubElement(outputemissions, "sourceusetype", selected="false")
        etree.SubElement(outputemissions, "movesvehicletype", selected="false")
        etree.SubElement(outputemissions, "onroadscc", selected="false")
        estimateduncer = etree.SubElement(outputemissions, "estimateuncertainty", selected="false")
        estimateduncer.set("numberOfIterations", "2")
        estimateduncer.set("keepSampledData", "false")
        estimateduncer.set("keepIterations", "false")
        etree.SubElement(outputemissions, "sector", selected="false")
        etree.SubElement(outputemissions, "engtechid", selected="false")
        etree.SubElement(outputemissions, "hpclass", selected="false")
        etree.SubElement(outputemissions, "regclassid", selected="false")

        # Create XML element tree for MOVES output database information
        outputdatabase = etree.Element("outputdatabase", servername=self.db_host)
        outputdatabase.set("databasename", self.moves_output_db)
        outputdatabase.set("description", "")

        # Create XML element tree for MOVES input database information
        scaleinput = etree.Element("scaleinputdatabase", servername=self.db_host)
        scaleinput.set("databasename", "fips_{fips}_{year}_in".format(fips=fips, year=self.year))
        scaleinput.set("description", "")

        # Create XML element tree for units used for MOVES output
        outputfactors = etree.Element("outputfactors")
        timefac = etree.SubElement(outputfactors, "timefactors", selected="true")
        timefac.set("units", "Hours")
        disfac = etree.SubElement(outputfactors, "distancefactors", selected="true")
        disfac.set("units", "Miles")
        massfac = etree.SubElement(outputfactors, "massfactors", selected="true")
        massfac.set("units", "Grams")
        massfac.set("energyunits", "Joules")

        # Create XML element trees for other MOVES runspec inputs

        # generate database with other outputs (leave empty)
        gendata = etree.Element("generatordatabase", shouldsave="false")
        gendata.set("servername", "")
        gendata.set("databasename", "")
        gendata.set("description", "")

        # lookupflags for database
        lookupflag = etree.Element("lookuptableflags", scenarioid=_scenid)
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
        etree.SubElement(timespan, "year", key=self.year.__str__())

        # loop through months
        etree.SubElement(timespan, "month", id=self.month.__str__())

        # loop through days (2 = weekend; 5 = weekday)
        etree.SubElement(timespan, "day", id=self.day.__str__())

        # loop through start hours
        etree.SubElement(timespan, "beginhour", id=self.beginning_hour.__str__())

        # loop through end hours
        etree.SubElement(timespan, "endhour", id=self.ending_hour.__str__())

        # aggregate at hourly level
        etree.SubElement(timespan, "aggregateBy", key="Hour")

        # Create XML element tree for MOVES vehicle type
        # @TODO connect all of these items back to user input
        # @NOTE can lists instead of individual types be specified here -
        # for running multiple vehicle types?
        # XML for vehicle type selections
        # combination short-haul truck
        vehicle_selection = etree.Element("onroadvehicleselection",
                                          fueltypeid=self.fuel_supply_fuel_type_id.__str__())
        vehicle_selection.set("fueltypedesc", "Diesel Fuel")
        vehicle_selection.set("sourcetypeid", self.source_type_id.__str__())
        vehicle_selection.set("sourcetypename", "Combination Short-haul Truck")

        # Create XML element tree for MOVES pollutant processes
        # Currently includes: CO, NH3, PM10, PM2.5, SO2, NOX, VOC,
        # and prerequisites

        # XML for pollutant process associations
        # create element for pollutant process associations
        polproc = etree.Element("pollutantprocessassociations")

        # populate subelements for pollutant processes
        # loop through all pollutants
        for _pol in self.polname:
            # loop through all processes associated with each pollutant
            for _proc in self.prockey[_pol]:
                pollutant = etree.SubElement(polproc,
                                             "pollutantprocessassociation",
                                             pollutantkey=self.polkey[_pol])
                pollutant.set("pollutantname", self.polname[_pol])
                pollutant.set("processkey", _proc)
                pollutant.set("processname", self.procname[_proc])

        # Create XML element tree for MOVES road types
        # dictionary for road types

        # XML for road types
        roadtypes = etree.Element("roadtypes", {"separateramps": "false"})
        for _roads in self.roaddict:
            roadtype = etree.SubElement(roadtypes, "roadtype", roadtypeid=_roads)
            roadtype.set("roadtypename", self.roaddict[_roads])
            roadtype.set("modelCombination", "M1")

        # Create XML element tree for extra database information (leave empty)
        inputdatabase = etree.Element("inputdatabase", servername="")
        inputdatabase.set("databasename", "")
        inputdatabase.set("description", "")

        # Create full element tree for MOVES import file
        _runspecfilestring = (
            E.runspec(
                    description,
                    E.models(etree.Element("model", value="ONROAD")),
                    etree.Element("modelscale", value="Rates"),
                    etree.Element("modeldomain", value="SINGLE"),
                    E.geographicselections(geoselect),
                    timespan,
                    E.onroadvehicleselections(vehicle_selection),
                    E.offroadvehicleselections(""),
                    E.offroadvehiclesccs(""),
                    roadtypes,
                    polproc,
                    E.databaseselections(""),
                    E.internalcontrolstrategies(internalcontrol),
                    inputdatabase,
                    uncertaintyparam,
                    etree.Element("geographicoutputdetail", description="LINK"),
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
                    scaleinput,
                    etree.Element("pmsize", value="0"),
                    outputfactors,
                    E.savedata(""),
                    E.donotexecute(""),
                    gendata,
                    etree.SubElement(gendata, "donotperformfinalaggregation", selected="false"),
                    lookupflag,
                    version=self.moves_version)
        )

        # Transform element tree to string and save to file

        # create string from element tree
        _stringout = etree.tostring(_runspecfilestring, pretty_print=True,
                                    encoding='utf8')

        # create filename for runspec file using FIPS and scenario year
        self.runspec_filename = os.path.join(self.save_path_runspecfiles,
                                         '{fips}_runspec_{year}.mrs'.format(
                                                 fips=fips, year=self.year))

        # save string to file
        with open(self.runspec_filename, 'wb') as _fileout:
            _fileout.write(_stringout)
            _fileout.close()

    def _get_cached_results(self):
        """

        :return: list of FIPS for which MOVES results already exist
        """

        # initialize kvals dict for SQL statement formatting
        kvals = dict()
        kvals['moves_output_db'] = self.moves_output_db
        kvals['year'] = self.year
        kvals['month'] = self.month
        kvals['day'] = self.day

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
              WHERE dist_table.yearID = {year} AND dist_table.monthID = {month}
               AND dist_table.dayID = {day};""".format(**kvals)

        # read in the table and get the list of unique FIPS for which
        # results already exist (takes year, month, day into account)
        _fips_cached = pd.read_sql(_results_fips_sql, self._conn).fips.unique()

        return _fips_cached

    def postprocess(self):
        """
        pulls moves output from database
        user input y/n: clear out old moves results
        postprocesses local copy to get rate per vehicle-mile by FIPS (saves
        this locally) and sends to routing for total emissions calculation
        :return: dataframe of postprocessed transportation emissions
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
        kvals['month'] = self.month
        kvals['day'] = self.day

        # some minor changes to the SQL tables in _moves_table_list
        _moves_cursor = self._conn.cursor()

        for _table in _moves_table_list:

            # LOGGER.debug('Adding fips column to {t}'.format(t=_table))
            _add_fips_sql = """ALTER TABLE {moves_output_db}.{t}
                                ADD COLUMN fips char(5);""".format(t=_table,
                                                                   **kvals)

            # LOGGER.debug('Updating fips column to {t}'.format(t=_table))
            _update_fips_sql = """UPDATE {moves_output_db}.{t}
                    SET fips = LEFT(MOVESScenarioID, 5);""".format(t=_table,
                                                                   **kvals)

            # test if the table already has a fips column; if so, go to update
            # table; if not, create the fips column
            try:
                _moves_cursor.execute(_add_fips_sql)

            except pymysql.err.InternalError:
                pass

            _moves_cursor.execute(_update_fips_sql)

        # close cursor after updating both tables
        _moves_cursor.close()

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
              WHERE dist_table.yearID = {year} AND dist_table.monthID = {month}
               AND dist_table.dayID = {day};""".format(**kvals)

        # read in all possibly relevant entries from the rate per distance
        # table
        _rateperdistance_all = pd.read_sql(_rateperdistance_table_sql, self._conn)

        # create a filter for relevant rateperdistance rows based on which
        # fips in rateperdistance are equal to fips in the moves run list
        _rateperdistance_filter = _rateperdistance_all.fips.isin(
            self.moves_run_list.MOVES_run_fips)

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
              WHERE veh_table.yearID = {year} AND veh_table.monthID = {month} 
              AND veh_table.dayID = {day};""".format(**kvals)

        _ratepervehicle_all = pd.read_sql(_ratepervehicle_table_sql, self._conn)

        _ratepervehicle_filter = _ratepervehicle_all.fips.isin(
            self.moves_run_list.MOVES_run_fips)

        _ratepervehicle = _ratepervehicle_all[_ratepervehicle_filter]

        LOGGER.debug('Postprocessing MOVES output')

        # add state column to both tables by pulling out first two digits of
        #  MOVESScenarioID
        _rateperdistance['state'] = _rateperdistance.MOVESScenarioID.str.slice(stop=2)
        _ratepervehicle['state'] = _ratepervehicle.MOVESScenarioID.str.slice(stop=2)

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
                                    self._conn).merge(self.roadtypevmt, on='roadTypeID')

        # Calculate total running emissions per trip (by pollutant)
        # Equal to sum(ratePerDistance * vmtfrac_in_speedbin[i] * vmt)
        # for all speed bins, pollutant processes, day types, hours,
        # and road types
        _join_dist_avgspd = _rateperdistance.merge(_averagespeed,
                                                   on=('roadTypeID',
                                                       'avgSpeedBinID',
                                                       'dayID',
                                                       'hourID'))

        # calculate non-summed rate per distance
        _join_dist_avgspd.eval('averageRatePerDistance = ratePerDistance * '
                               'avgSpeedFraction * '
                               'roadTypeVMTFraction', inplace=True)

        # calculate final pollutant rates per distance by grouping and
        # summing rates per distance over pollutant processes, hours,
        # speed bins, and road types to get one rate per
        # fips-month-day-pollutant combo
        _avgRateDist = _join_dist_avgspd.groupby(['fips',
                                                  'state',
                                                  'yearID',
                                                  'monthID',
                                                  'dayID',
                                                  'pollutantID'],
                                                 as_index=False).sum()[['fips',
                                                                        'state',
                                                                        'pollutantID',
                                                                        'averageRatePerDistance']]

        # calculate final pollutant rates per distance
        _avgRateDist = _join_dist_avgspd.sum()[['fips', 'state',
                                                'pollutantID',
                                                'averageRatePerDistance']]

        # merge with the pollutant names dataframe
        _avgRateDist = _avgRateDist.merge(self.pollutant_names, how='inner',
                                          on='pollutantID')

        # merge the truck capacity numbers with the rate per distance merge
        # to prep for calculating number of trips
        _run_emissions = _avgRateDist.merge(self.prod_moves_runs[['MOVES_run_fips',
                                                     'state',
                                                     'region_production',
                                                     'region_destination',
                                                     'feedstock',
                                                     'tillage_type',
                                                     'feedstock_amount']], how='left',
                                            left_on=['fips', 'state'],
                                            right_on=['MOVES_run_fips',
                                                      'state']).merge(
                self.truck_capacity[['feedstock',
                                     'truck_capacity']],
                how='left',
                on='feedstock')

        # get routing information between each unique region_production and
        # region_destination pair
        _routes = _run_emissions[['region_production',
                                  'region_destination']].drop_duplicates()

        # use the region-fips map to generate fips_production and
        # fips_destination columns
        _routes = _routes.merge(self.region_fips_map, how='left',
                                left_on='region_production',
                                right_on='region')
        _routes.rename(index=str, columns={'fips': 'fips_production'},
                       inplace=True)

        _routes = _routes.merge(self.region_fips_map, how='left',
                                left_on='region_destination',
                                right_on='region')[['region_production',
                                            'region_destination',
                                            'fips_production',
                                            'fips']]
        _routes.rename(index=str, columns={'fips': 'fips_destination'},
                       inplace=True)

        # if routing engine is specified, use it to get the route (fips and
        # vmt) for each unique region_production and region_destination pair
        if self.router:

            # initialize holder for all routes
            _vmt_by_county_all_routes = pd.DataFrame()

            # loop through all routes
            for i in np.arange(_routes.shape[0]):

                # use the routing engine to get a route
                _vmt_by_county = self.router.get_route(from_fips=_routes.fips_production.iloc[i],
                                                       to_fips=_routes.fips_destination.iloc[i])

                # add identifier columns for later merging with _run_emissions
                _vmt_by_county['region_production'] = _routes.region_production.iloc[i]
                _vmt_by_county['region_destination'] = _routes.region_destination.iloc[i]

                # either create the data frame to store all routes,
                # or append the current route
                if _vmt_by_county_all_routes.empty:
                    _vmt_by_county_all_routes = _vmt_by_county

                else:
                    _vmt_by_county_all_routes = \
                        _vmt_by_county_all_routes.append(_vmt_by_county,
                                                         ignore_index=True,
                                                         sort=True)

            # after the loop through all routes is complete, merge the data
            # frame containing all routes with _run_emissions
            _run_emissions = _run_emissions.merge(_vmt_by_county_all_routes,
                                                  how='left',
                                                  on=['region_production',
                                                      'region_destination'])

        else:
            # if no routing engine is specified, use the user-specified vmt
            # and fill the region_transportation column with blank cells
            _run_emissions['region_transportation'] = None
            _run_emissions['vmt'] = self.vmt_short_haul

        # evaluate running emissions
        _run_emissions.eval('pollutant_amount = averageRatePerDistance * vmt *'
                            ' feedstock_amount / truck_capacity',
                            inplace=True)

        # start and hotelling emissions
        _avgRateVeh = _ratepervehicle.groupby(['fips', 'state', 'yearID',
                                               'monthID', 'dayID',
                                               'pollutantID'],
                                              as_index=False).sum(
            inplace=True)[['fips', 'state', 'pollutantID', 'ratePerVehicle']]

        _avgRateVeh = _avgRateVeh.merge(self.pollutant_names, how='inner',
                                        on='pollutantID')

        # merge raw moves output with production data and truck capacities
        _start_hotel_emissions = _avgRateVeh.merge(self.prod_moves_runs,
                                                   how='left',
                                                   left_on=['fips', 'state'],
                                                   right_on=['MOVES_run_fips',
                                                             'state']).merge(
            self.truck_capacity[['feedstock', 'truck_capacity']],
            how='left',
            on='feedstock')

        # calculate start and hotelling emissions
        _start_hotel_emissions.eval('pollutant_amount = ratePerVehicle * '
                                    'feedstock_amount / truck_capacity',
                                    inplace=True)

        # append the run emissions with the start and hotelling emissions
        _transportation_emissions = pd.concat([_run_emissions[['region_production',
                                                               'region_destination',
                                                               'feedstock',
                                                               'tillage_type',
                                                               'region_transportation',
                                                               'pollutant',
                                                               'pollutant_amount']],
                                               _start_hotel_emissions[['region_production',
                                                                       'region_destination',
                                                                       'feedstock',
                                                                       'tillage_type',
                                                                       'pollutant',
                                                                       'pollutant_amount']]],
                                              ignore_index=True, sort=True)

        # add activity and module columns
        _transportation_emissions['activity'] = 'transportation'
        _transportation_emissions['module'] = 'moves'

        # convert pollutant amounts from grams (calculated by MOVES) to pounds
        _transportation_emissions['pollutant_amount'] = \
            _transportation_emissions['pollutant_amount'] * \
            self.conversion_factors['gram']['pound']

        # sum up by pollutant type for final module output
        _transportation_emissions = _transportation_emissions.groupby(
            ['region_production', 'region_destination', 'feedstock',
             'tillage_type', 'module', 'region_transportation', 'pollutant'],
            as_index=False).sum()

        return _transportation_emissions

    def run(self):
        """
        Prepare and execute MOVES.

        :return:
        """

        # generate a list of FIPS-state combinations for which MOVES
        # will be run

        # add a column with the state code to the region-to-fips df
        self.region_fips_map['state'] = self.region_fips_map.fips.str[0:2]

        # merge the feedstock_measure_type rows from production with the
        # region-FIPS map
        _prod_merge = self.production[self.production.feedstock_measure ==
                                      self.feedstock_measure_type].merge(self.region_fips_map,
                                                                         left_on='region_production',
                                                                         right_on='region')

        # sum all feedstock production within each FIPS-year combo (also
        # grouping by state just pulls that column along, it doesn't change
        # the grouping)
        # this gets saved in self for use in postprocessing
        _prod_by_fips_feed = _prod_merge.groupby(['fips',
                                                  'state',
                                                  'feedstock'],
                                                 as_index=False).sum()

        # within each FIPS-year-feedstock combo, find the highest
        # feedstock production
        _max_amts_feed = _prod_by_fips_feed.groupby(['state',
                                                     'feedstock'],
                                                    as_index=False).max()

        if self.moves_by_state:
            # sum total feedstock production within each fips-state-year combo
            _amts_by_fips = _prod_by_fips_feed.groupby(['fips',
                                                        'state'],
                                                       as_index=False).sum()

            # locate the fips within each state with the highest total
            # feedstock production
            _max_amts = _amts_by_fips.groupby(['state'],
                                              as_index=False).max()

            # strip out duplicates (shouldn't be any) to create a list of
            # unique fips-state combos to run MOVES on
            self.moves_run_list = _max_amts[['fips',
                                             'state']].drop_duplicates()
        elif self.moves_by_state_and_feedstock:
            # get a list of unique fips-state-year combos to run MOVES on
            # keep feedstock in there to match results from each MOVES run
            # to the correct set of feedstock production data
            self.moves_run_list = _max_amts_feed[['fips',
                                                  'state',
                                                  'feedstock']].drop_duplicates()
        else:
            # if neither moves_by_state nor moves_by_state_and_feedstock are True,
            # the fips-state-year combos to run MOVES on come straight from
            # the production data
            self.moves_run_list = _prod_merge[['fips',
                                               'state']].drop_duplicates()

        # rename the fips and state columns for easier merging with the
        # production df
        self.moves_run_list.rename(index=str,
                                   columns={'fips': 'MOVES_run_fips',
                                            'state': 'MOVES_run_state'},
                                   inplace=True)

        # merge production with moves run fips and states and save in self
        # for use in postprocessing
        self.prod_moves_runs = _prod_merge.merge(self.moves_run_list,
                                                 left_on='state',
                                                 right_on='MOVES_run_state')[
            ['fips',
             'MOVES_run_fips',
             'state',
             'region_production',
             'region_destination',
             'tillage_type',
             'feedstock',
             'feedstock_measure',
             'feedstock_amount']].drop_duplicates()

        # @NOTE prod_moves_runs is being stored in self as a potential
        # output or check on functionality; it'll also be used in
        # postprocessing

        # after generating the list of FIPS over which MOVES is run,
        # begin to create the input data and run MOVES

        if self.use_cached_results:
            # run only fips for which there are no cached results
            # @TODO implement: subset and redefine moves_run_list, 
            # excluding those fips for which results already exist

            _exclude_fips = self._get_cached_results()

            # report that MOVES run already complete
            _kvals = {'h': self.config.get('moves_db_host'),
                      'db': self.config.get('moves_database'),
                      'f': _exclude_fips}
            LOGGER.info('using cached results from %(h)s/%(db)s for FIPS: %(f)s)' % _kvals)
            # create shortened list of fips to run through MOVES
            _run_fips = [x for x in self.moves_run_list.MOVES_run_fips
                         if x not in _exclude_fips]
        else:
            # run all fips regardless of whether cached results exist or not
            _run_fips = list(self.moves_run_list.MOVES_run_fips)

        # only go through the setup and run steps if there are fips that
        # need to be run
        if _run_fips.__len__() > 0:
            # create national datasets only once per FPEAM
            self._create_national_data()

            # loop through rows of moves_run_list to generate input data files
            # for each FIPS
            for _fips in _run_fips:
                # create county-level data files
                self._create_county_data(fips=_fips)

                # create XML import files
                self._create_xml_import(fips=_fips)

                # create XML run spec files
                self._create_xml_runspec(fips=_fips)

                # actually send the commands to import files into MOVES and
                # then run MOVES

                # import MOVES data into datbase
                LOGGER.info('importing MOVES files for FIPS: %s' % _fips)
                LOGGER.debug('import file: %s' % self.xmlimport_filename)

                # import data and log output
                command = 'cd {moves_path} & setenv.bat & ' \
                          'java -Xmx512M ' \
                          'gov.epa.otaq.moves.master.commandline.MOVESCommandLine -i {import_file}' \
                          ''.format(moves_path=self.moves_path,
                                    import_file=self.xmlimport_filename)
                os.system(command)  # @TODO: need to capture output, catch errors

                # execute MOVES and log output
                LOGGER.info('running MOVES for FIPS: %s' % _fips)
                LOGGER.debug('runspec file: %s' % self.runspec_filename)

                command = 'cd {moves_folder} & setenv.bat & ' \
                          'java -Xmx512M ' \
                          'gov.epa.otaq.moves.master.commandline.MOVESCommandLine ' \
                          '-r {run_moves}'.format(
                           moves_folder=self.moves_path,
                           run_moves=self.runspec_filename)

                os.system(command)  # @TODO: need to capture output, catch errors

        # postprocess output
        _results = None
        _status = self.status
        e = None

        try:
            _results = self.postprocess()
        except Exception as e:
            LOGGER.exception(e)
            _status = 'failed'
        else:
            _status = 'complete'
        finally:
            self.status = _status
            self.results = _results
            if e:
                raise e

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        # close connection to MOVES database
        self._conn.close()

        # process exceptions
        if exc_type is not None:
            LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self
