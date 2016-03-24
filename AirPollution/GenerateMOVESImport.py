# -*- coding: utf-8 -*-
"""
Created on Fri Feb 12 09:49:39 2016

Generates XML file for MOVES importer

Inputs include: 
    crop type (for filenames)
    fips code (for filenames and input data)
    timespan for MOVES analysis (moves_timespan: year(s), month(s), day(s), and hour(s))
    paths for all input data (e.g., agefilename, speedfilename)
    path for saving XML file (filename under function: create_import_file)  
Output: 
    formatted xml file with name of fips code_import_year_crop.mrs (e.g., "19109_import_2015_CG.mrs")

@author: aeberle
"""
from lxml import etree
from lxml.builder import E


class GenerateMOVESImport: 
    """
    Generate XML file that allows MOVES County Data Manager to be used from command line
    """
    
    def __init__(self, crop, fips, yr, moves_timespan, agefilename, speedfilename, fuelsupfilename, fuelformfilename, fuelusagefilename, avftfilename, metfilename,
                 roadtypefilename, sourcetypefilename, vmtfilename, monthvmtfilename, dayvmtfilename, hourvmtfilename):
        """

        :param crop:
        :param fips:
        :param yr:
        :param moves_timespan:
        :param agefilename:
        :param speedfilename:
        :param fuelsupfilename:
        :param fuelformfilename:
        :param fuelusagefilename:
        :param avftfilename:
        :param metfilename:
        :param roadtypefilename:
        :param sourcetypefilename:
        :param vmtfilename:
        :param monthvmtfilename:
        :param dayvmtfilename:
        :param hourvmtfilename:
        :return:
        """

        # set parser to leave CDATA sections in document 
        self.parser = etree.XMLParser(strip_cdata=False, recover=True)
        
        # create XML for elements with CDATA
        self.internalcontrol = etree.XML('<internalcontrolstrategy classname="gov.epa.otaq.moves.master.implementation.ghg.internalcontrolstrategies.rateofprogress.RateOfProgressStrategy"><![CDATA[useParameters	No]]></internalcontrolstrategy>', self.parser)
        self.agename = "<filename>{agefilename}</filename>".format(agefilename=agefilename)
        self.agefile = etree.XML(self.agename, self.parser)
        self.speedfile = etree.XML("<filename>{speedfilename}</filename>".format(speedfilename=speedfilename), self.parser)
        self.fuelsupfile = etree.XML("<filename>{fuelsupfilename}</filename>".format(fuelsupfilename=fuelsupfilename), self.parser)
        self.fuelformfile = etree.XML("<filename>{fuelformfilename}</filename>".format(fuelformfilename=fuelformfilename), self.parser)
        self.fuelusagefile = etree.XML("<filename>{fuelusagefilename}</filename>".format(fuelusagefilename=fuelusagefilename), self.parser)
        self.avftfile = etree.XML("<filename>{avftfilename}</filename>".format(avftfilename=avftfilename), self.parser)
        self.metfile = etree.XML("<filename>{metfilename}</filename>".format(metfilename=metfilename), self.parser)
        self.roadtypefile = etree.XML("<filename>{roadtypefilename}</filename>".format(roadtypefilename=roadtypefilename), self.parser)
        self.sourcetypefile = etree.XML("<filename>{sourcetypefilename}</filename>".format(sourcetypefilename=sourcetypefilename), self.parser)
        self.HPMSyearfile = etree.XML("<filename>{vmtfilename}</filename>".format(vmtfilename=vmtfilename), self.parser)
        self.monthVMTfile = etree.XML("<filename>{monthvmtfilename}</filename>".format(monthvmtfilename=monthvmtfilename), self.parser)
        self.dayVMTfile = etree.XML("<filename>{dayvmtfilename}</filename>".format(dayvmtfilename=dayvmtfilename), self.parser)
        self.hourVMTfile = etree.XML("<filename>{hourvmtfilename}</filename>".format(hourvmtfilename=hourvmtfilename), self.parser)
        
        # variables for MOVES runs
        self.fips = fips  # FIPS code
        self.yr = yr  # scenario year
        self.mo = moves_timespan['mo']  # month(s) for analysis
        self.d = moves_timespan['d']  # days(s) for analysis
        self.bhr = moves_timespan['bhr']  # beginning hour(s) for analysis
        self.ehr = moves_timespan['ehr']  # ending hour(s) for analysis
        
        self.db_in = "fips_{fips}_{crop}_in".format(fips=fips, crop=crop)  # input database for MOVES runs
        self.scenid = "{fips}_{crop}_{year}_{month}_{day}".format(fips=fips, crop=crop, day=self.d, month=self.mo, year=self.yr)  # scenario ID for MOVES runs
    
    def geo_selection(self):
        """
        Create XML element tree for geographic selection

        :return:  element
        """

        # XML for geographic selection
        geoselect = etree.Element("geographicselection", type="COUNTY")
        geoselect.set("key", self.fips)
        geoselect.set("description", "")

        return geoselect
        
    def timespan(self):
        """
        Create XML element tree for MOVES timespan

        :return: XML element
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

    def vehtype(self):
        """
        Create XML element tree for MOVES vehicle type
        Currently only for combination short-haul truck

        :return: XML element
        """

        # XML for vehicle type selections
        # combination short-haul truck
        com_sh_truck = etree.Element("onroadvehicleselection", fueltypeid="2")
        com_sh_truck.set("fueltypedesc", "Diesel Fuel")
        com_sh_truck.set("sourcetypeid", "61")
        com_sh_truck.set("sourcetypename", "Combination Short-haul Truck")

#        # light commercial truck
#        lt_com_truck = etree.Element("onroadvehicleselection", fueltypeid="2")
#        lt_com_truck.set("fueltypedesc", "Diesel Fuel")
#        lt_com_truck.set("sourcetypeid","32")
#        lt_com_truck.set("sourcetypename","Light Commercial Truck")

        return com_sh_truck

    def pollutantprocess(self):
        """
        Create XML element tree for MOVES pollutant processes
        Currently includes: CO, NH3, PM10, PM2.5, SO2, NOX, VOC, and prerequisites

        :return:
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

    def roadtypes(self):
        """
        Create XML element tree for MOVES road types

        :return: XML element
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
            
    def databaseinfo(self): 
        """
        Create XML element tree for MOVES input database information

        :return: XML element
        """

        # XML for database selection
        databasesel = etree.Element("databaseselection", servername="localhost")
        databasesel.set("databasename", self.db_in)

        return databasesel
        
    def agedist(self):
        """
        Create XML element tree for MOVES vehicle age distribution

        :return: XML element

        """
        # XML for age distribution
        agedist = etree.Element("agedistribution")
        etree.SubElement(agedist, "description")
        part = etree.SubElement(agedist, "parts")
        std = etree.SubElement(part, "sourceTypeAgeDistribution")
        etree.SubElement(std, "filename")

        return agedist

    def fullimport(self): 
        """
        Create full element tree for MOVES import file

        :return:

        """
        geoselect = self.geo_selection
        timespan = self.timespan        
        com_sh_truck = self.vehtype
        roadtypes = self.roadtypes
        polproc = self.pollutantprocess
        databasesel = self.databaseinfo
        
        # generate element tree for import run spec
        importfilestring = (
                            E.moves(
                                    E.importer(
                                                E.filters(
                                                            E.geographicselections(geoselect),
                                                            timespan,
                                                            E.onroadvehicleselections(com_sh_truck),
                                                            E.offroadvehicleselections(""),
                                                            E.offroadvehiclesccs(""),
                                                            roadtypes,
                                                            polproc,
                                                            ),
                                                databasesel,
                                                E.agedistribution(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(E.sourceTypeAgeDistribution(self.agefile))),
                                                E.avgspeeddistribution(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(E.avgSpeedDistribution(self.speedfile))),
                                                E.fuel(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(
                                                           E.FuelSupply(self.fuelsupfile),
                                                           E.FuelFormulation(self.fuelformfile),
                                                           E.FuelUsageFraction(self.fuelusagefile),
                                                           E.AVFT(self.avftfile),
                                                                )),
                                                E.zoneMonthHour(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(E.zonemonthhour(self.metfile))),
                                                E.rampfraction(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(E.roadType(E.filename("")))),
                                                E.roadtypedistribution(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(E.roadTypeDistribution(self.roadtypefile))),
                                                E.sourcetypepopulation(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(E.sourceTypeYear(self.sourcetypefile))),
                                                E.starts(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(
                                                           E.startsPerDay(E.filename("")),
                                                           E.startsHourFraction(E.filename("")),
                                                           E.startsSourceTypeFraction(E.filename("")),
                                                           E.startsMonthAdjust(E.filename("")),
                                                           E.importStartsOpModeDistribution(E.filename("")),
                                                           E.Starts(E.filename("")),
                                                                )),
                                                E.vehicletypevmt(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(
                                                                E.HPMSVtypeYear(self.HPMSyearfile),
                                                                E.monthVMTFraction(self.monthVMTfile),
                                                                E.dayVMTFraction(self.dayVMTfile),
                                                                E.hourVMTFraction(self.hourVMTfile),
                                                                )),
                                                E.hotelling(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(
                                                                E.hotellingActivityDistribution(E.filename("")),
                                                                E.hotellingHours(E.filename("")))),
                                                E.imcoverage(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(E.IMCoverage(E.filename("")))),
                                                E.onroadretrofit(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(E.onRoadRetrofit(E.filename("")))),
                                                E.generic(
                                                        etree.XML('<description><![CDATA[]]></description>', self.parser),
                                                        E.parts(E.anytable(E.tablename("agecategory"), E.filename("")))),
                                                mode="county")
                                    )
                                )
        return importfilestring
                
    def create_import_file(self, filename):
        """
        Transform element tree to string and save to file

        :param filename = filename for import XML file
        """        

        # generate XML element tree
        importfilestring = GenerateMOVESImport.fullimport(self)

        # create string from element tree
        stringout = etree.tostring(importfilestring, pretty_print=True, encoding='utf8')

        # save string to file
        fileout = open(filename, "w")
        fileout.write(stringout)
        fileout.close()
