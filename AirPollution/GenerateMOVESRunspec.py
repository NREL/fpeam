# -*- coding: utf-8 -*-
"""
Created on Fri Feb 12 09:49:39 2016

Generates XML file for MOVES runspec

Inputs include: 
    crop type
    FIPS code
    scenario year
    timespan for MOVES analysis (moves_timespan: month(s), day(s), and hour(s))
    MOVES server
    path for saving (filename under function: "create_runspec_files")   
Output: 
    formatted xml file with name of FIPS code_runspec_year_crop.mrs (e.g., "19109_runspec_2015_CG.mrs") 

@author: aeberle
"""
from lxml import etree
from lxml.builder import E
from src.AirPollution import utils

class GenerateMOVESRunSpec:
    """
    Generate XML file for running MOVES from the command line
    """

    def __init__(self, crop, fips, yr, moves_timespan, server):
        config = utils.config
        self.db_in = "fips_{fips}_{crop}_in".format(fips=fips, crop=crop)  # input database
        self.db_out = "{moves_output_db}".format(moves_output_db=config.get('moves_output_db'))  # output database
        self.yr = yr  # scenario year
        self.mo = moves_timespan['mo']  # month(s) for analysis
        self.d = moves_timespan['d']  # days(s) for analysis
        self.bhr = moves_timespan['bhr']  # beginning hour(s) for analysis
        self.ehr = moves_timespan['ehr']  # ending hour(s) for analysis
        self.FIPS = fips  # FIPS code
        self.server = server  # host for MOVES server
        self.scenid = "{fips}_{crop}_{year}_{month}_{day}".format(fips=fips, crop=crop, day=self.d[0], month=self.mo[0], year=self.yr)  # scenario ID for MOVES runs

        # set parser to leave CDATA sections in document
        self.parser = etree.XMLParser(strip_cdata=False)

    def cdata(self):
        """
        Create XML element tree for elements with MOVES inputs with CDATA
        """
        description = etree.XML('<description><![CDATA[]]></description>', self.parser)
        internalcontrol = etree.XML('<internalcontrolstrategy classname="gov.epa.otaq.moves.master.implementation.ghg.internalcontrolstrategies.rateofprogress.RateOfProgressStrategy"><![CDATA[useParameters	No]]></internalcontrolstrategy>', self.parser)
        
        return description, internalcontrol
    
    def uncertainty_param(self):
        """
        Create XML element tree for MOVES uncertainty parameters
        """
        uncertaintyparam = etree.Element("uncertaintyparameters", uncertaintymodeenabled="false")
        uncertaintyparam.set("numberofrunspersimulation", "0")
        uncertaintyparam.set("numberofsimulations", "0")
        
        return uncertaintyparam
    
    def emission_breakdown(self):
        """
        Create XML element tree for MOVES output emissions breakdown, which specifies which outputs are included in MOVES analysis
        """
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

        return outputemissions
        
    def output_database(self):
        """
        Create XML element tree for MOVES output database information
        """
        outputdatabase = etree.Element("outputdatabase", servername=self.server)
        outputdatabase.set("databasename", self.db_out)
        outputdatabase.set("description", "")
        
        return outputdatabase
    
    def input_database(self):
        """
        Create XML element tree for MOVES input database information
        """
        scaleinput = etree.Element("scaleinputdatabase", servername=self.server)
        scaleinput.set("databasename", self.db_in)
        scaleinput.set("description", "")
        
        return scaleinput 
        
    def units(self):
        """
        Create XML element tree for units used for MOVES output
        """
        outputfactors = etree.Element("outputfactors")
        timefac = etree.SubElement(outputfactors, "timefactors", selected="true")
        timefac.set("units", "Hours")
        disfac = etree.SubElement(outputfactors, "distancefactors", selected="true")
        disfac.set("units", "Miles")
        massfac = etree.SubElement(outputfactors, "massfactors", selected="true")
        massfac.set("units", "Grams")
        massfac.set("energyunits", "Joules")
        
        return outputfactors 
    
    def other(self):
        """
        Create XML element trees for other MOVES runspec inputs
        """
        # generate database with other outputs (leave empty)
        gendata = etree.Element("generatordatabase", shouldsave="false")
        gendata.set("servername", "")
        gendata.set("databasename", "")
        gendata.set("description", "")
        
        # lookupflags for database
        lookupflag = etree.Element("lookuptableflags", scenarioid=self.scenid)
        lookupflag.set("truncateoutput", "true")
        lookupflag.set("truncateactivity", "true")
        lookupflag.set("truncatebaserates", "true")
        
        return gendata, lookupflag

    def geo_selection(self):
        """
        Create XML element tree for MOVES geographic selection
        """
        geoselect = etree.Element("geographicselection", type="COUNTY")
        geoselect.set("key", self.FIPS)
        geoselect.set("description", "")
        
        return geoselect
        
    def time_span(self):
        """
        Create XML element tree for MOVES timespan
        """
        # XML for timespan
        timespan = etree.Element("timespan")
        # set year
        etree.SubElement(timespan, "year", key=self.yr)
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
        
        return timespan

    def veh_type(self):
        """
        Create XML element tree for MOVES vehicle type
        Currently only for combination short-haul truck 
        """ 
        # XML for vehicle type selections
        # combination short-haul truck
        com_sh_truck = etree.Element("onroadvehicleselection", fueltypeid="2")
        com_sh_truck.set("fueltypedesc", "Diesel Fuel")
        com_sh_truck.set("sourcetypeid", "61")
        com_sh_truck.set("sourcetypename", "Combination Short-haul Truck")
        
#        #light commercial truck
#        lt_com_truck = etree.Element("onroadvehicleselection", fueltypeid="2")
#        lt_com_truck.set("fueltypedesc", "Diesel Fuel")
#        lt_com_truck.set("sourcetypeid", "32")
#        lt_com_truck.set("sourcetypename", "Light Commercial Truck")
        
        return com_sh_truck

    def pollutant_process(self):
        """
        Create XML element tree for MOVES pollutant processes
        Currently includes: CO, NH3, PM10, PM2.5, SO2, NOX, VOC, and prerequisites 
        """
        # dictionary of pollutant shorthand to MOVES name
        polname = {"NH3": "Ammonia (NH3)",
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
        polkey = {"NH3": "30",
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
        procname = {"1": "Running Exhaust",
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
        prockey = {"NH3": ["1", "2", "15", "16", "17", "90", "91"],
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
        for pol in polname:  # loop through all pollutants
            for proc in prockey[pol]:  # loop through all processes associated with each pollutant
                pollutant = etree.SubElement(polproc, "pollutantprocessassociation", pollutantkey=polkey[pol])
                pollutant.set("pollutantname", polname[pol])
                pollutant.set("processkey", proc)
                pollutant.set("processname", procname[proc])
                
        return polproc

    def road_types(self):
        """
        Create XML element tree for MOVES road types
        """
        # dictionary for road types 
        roaddict = {"1": "Off-Network",
                    "2": "Rural Restricted Access",
                    "3": "Rural Unrestricted Access",
                    "4": "Urban Restricted Access",
                    "5": "Urban Unrestricted Access"}
        # XML for road types 
        roadtypes = etree.Element("roadtypes", {"separateramps": "false"})
        for roads in roaddict:  
            roadtype = etree.SubElement(roadtypes, "roadtype", roadtypeid=roads)
            roadtype.set("roadtypename", roaddict[roads])
            roadtype.set("modelCombination", "M1")
        
        return roadtypes
    
    def extra_input_database(self):
        """
        Create XML element tree for extra database information (leave empty)
        """
        inputdatabase = etree.Element("inputdatabase", servername="")
        inputdatabase.set("databasename", "")
        inputdatabase.set("description", "")
        
        return inputdatabase

    def full_runspec(self):
        """
        Create full element tree for MOVES import file
        """
        geoselect = self.geo_selection()
        timespan = self.time_span()
        com_sh_truck = self.veh_type()
        roadtypes = self.road_types()
        polproc = self.pollutant_process()
        [description, internalcontrol] = GenerateMOVESRunSpec.cdata(self)
        extrainputdatabase = self.extra_input_database()
        uncertaintyparam = self.uncertainty_param()
        outputdatabase = self.output_database()
        outputfactors = self.units()
        [gendata, lookupflag] = GenerateMOVESRunSpec.other(self)
        outputemissions = self.emission_breakdown()
        inputdatabase = self.input_database()
        
        runspecfile = (
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
                    com_sh_truck
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
                extrainputdatabase,
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
                inputdatabase,
                etree.Element("pmsize", value="0"),
                outputfactors,
                E.savedata(""
                           ),
                E.donotexecute(""
                               ),
                gendata,
                etree.SubElement(gendata, "donotperformfinalaggregation", selected="false"),
                lookupflag,        
                version="MOVES2014a-20151201")
                )
    
        return runspecfile 
    
    def create_runspec_files(self, filename):
        """
        Transform element tree to string and save to file
        @param filename = filename for run spec
        """   
        # generate XML element tree        
        runspecfilestring = GenerateMOVESRunSpec.full_runspec(self)
        # create string from element tree           
        stringout = etree.tostring(runspecfilestring, pretty_print=True, encoding='utf8')
        # save string to file      
        fileout = open(filename, "w")
        fileout.write(stringout)
        fileout.close()
