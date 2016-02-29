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

import MOVESBatch as MB
import GenerateMOVESImport as GenMOVESIm
import GenerateMOVESRunspec as GenMOVESRun
import os 
import csv
from src.AirPollution.utils import config, logger
import subprocess
import pymysql

class MOVESModule(): 
    """
    Generate XML files for import and runspec files and creates batch files for importing and running MOVES
    """
    
    def __init__(self,crop,FIPSlist,yr,path_MOVES,save_path_importfiles,save_path_runspecfiles,save_path_countyinputs,save_path_nationalinputs): 
        self.crop = crop # crop name   
        self.FIPSlist = FIPSlist # list of FIPS codes
        self.yr = yr # scenario year 
        self.path_MOVES = path_MOVES # path for MOVES program
        self.save_path_importfiles = save_path_importfiles # path for MOVES import files 
        self.save_path_runspecfiles = save_path_runspecfiles # path for MOVES runspec files
        self.save_path_countyinputs = save_path_countyinputs # path for MOVES county data input files
        self.save_path_nationalinputs = save_path_nationalinputs # path for national input data files for MOVES 
        self.model_run_title = config.get('title') # scenario title 
        self.MOVES_database = config.get('MOVES_database') # MOVES database name 
        self.MOVES_db_user = config.get('MOVES_db_user') # username for MOVES database
        self.MOVES_db_pass = config.get('MOVES_db_pass') # password for MOVES database
        self.MOVES_db_host = config.get('MOVES_db_host') # host for MOVES database
        self.MOVES_timespan = config.get('MOVES_timespan') # timespan for MOVES runs
        self.age_distribution = config.get('age_distribution') # age distribution dictionary for MOVES runs (varies by scenario year)
        
    def createcountydata(self, vmt_shorthaul, pop_shorthaul):
        """
        Create county-level data for MOVES, including: 
            vehicle miles travelled
            source type population 
            fuel supply type
            fuel formulation
            fuel usage fraction 
            meteorology         
        
        @param: vmt_shorthaul = annual vehicle miles traveled by combination short-haul trucks
        @param: pop_shorthaul = population of combination short-haul trucks
        """
        logger.info('Creating county-level data files for MOVES')      
        
        # connect to MOVES database
        connection = pymysql.connect(host=self.MOVES_db_host, user=self.MOVES_db_user,password=self.MOVES_db_pass,db=self.MOVES_database)
        cursor = connection.cursor()
        
        # set year for MOVES database queries 
        year = self.yr
        
        for FIPS in self.FIPSlist:        
            # define zoneID and countyID for querying MOVES database
            zoneID = FIPS + '0'
            countyID = FIPS
            kvals ={}
            kvals['year']=year
            kvals['MOVES_database']=self.MOVES_database
            kvals['countyID']=countyID
            kvals['zoneID']=zoneID
            """
            county-level input files for MOVES that vary by FIPS, year, and crop 
            (these inputs are calculated by FPEAM based on production data)
            """
            vmtname = os.path.join(self.save_path_countyinputs, FIPS+'_vehiclemiletraveled_'+self.yr+'_'+self.crop+'.csv')
            sourcetypename = os.path.join(self.save_path_countyinputs, FIPS+'_sourcetype_'+self.yr+'_'+self.crop+'.csv')
            
            # annual vehicle miles traveled by vehicle type 
            with open(vmtname,'wb') as csvfile:
                vmtwriter = csv.writer(csvfile, dialect='excel')
                vmtwriter.writerow(['HPMSVtypeID', 'yearID', 'HPMSBaseYearVMT'])
                vmtwriter.writerow(['60', self.yr, vmt_shorthaul]) # combination short-haul truck
            
            # source type population (number of vehicles by vehicle type)
            with open(sourcetypename,'wb') as csvfile:
                popwriter = csv.writer(csvfile, dialect='excel')
                popwriter.writerow(['yearID', 'sourceTypeID', 'sourceTypePopulation'])
                popwriter.writerow([self.yr,"61", pop_shorthaul]) # combination short-haul truck
            
            """
            county-level input files for MOVES that vary by FIPS and year
            """
            fuelsupplyname = os.path.join(self.save_path_countyinputs, FIPS+'_fuelsupply_'+self.yr+'_.csv')
            fuelformname = os.path.join(self.save_path_countyinputs, FIPS+'_fuelformulation_'+self.yr+'_'+self.crop+'.csv')
            fuelusagename = os.path.join(self.save_path_countyinputs, FIPS+'_fuelusagefraction_'+self.yr+'_'+self.crop+'.csv')
            # export county-level fuel supply data     
            with open(fuelsupplyname,'wb') as f:
                cursor.execute("""SELECT * FROM {MOVES_database}.fuelsupply
                                WHERE {MOVES_database}.fuelsupply.fuelRegionID =
                                (SELECT regionID FROM {MOVES_database}.regioncounty WHERE countyID = '{countyID}' AND fuelYearID='{year}')
                                AND {MOVES_database}.fuelsupply.fuelYearID = '{year}'""".format(**kvals))    
                csv_writer = csv.writer(f)
                csv_writer.writerow([i[0] for i in cursor.description]) # write headers
                csv_writer.writerows(cursor)
            
            # export county-level fuel formulation data 
            with open(fuelformname,'wb') as f:
                cursor.execute("""SELECT * FROM {MOVES_database}.fuelformulation
                                WHERE {MOVES_database}.fuelformulation.fuelSubtypeID = '21' 
                                OR {MOVES_database}.fuelformulation.fuelSubtypeID = '20';""".format(**kvals))    
                csv_writer = csv.writer(f)
                csv_writer.writerow([i[0] for i in cursor.description]) # write headers
                csv_writer.writerows(cursor)
                
            # export county-level fuel usage fraction data 
            with open(fuelusagename,'wb') as f:
                cursor.execute("""SELECT * FROM {MOVES_database}.fuelusagefraction
                                WHERE {MOVES_database}.fuelusagefraction.countyID='{countyID}' 
                                AND {MOVES_database}.fuelusagefraction.fuelYearID = '{year}'
                                AND {MOVES_database}.fuelusagefraction.fuelSupplyFuelTypeID = '2';""".format(**kvals))    
                csv_writer = csv.writer(f)
                csv_writer.writerow([i[0] for i in cursor.description]) # write headers
                csv_writer.writerows(cursor)
                
            """
            county-level input files for MOVES that vary by FIPS
            """
            metname = os.path.join(self.save_path_countyinputs, FIPS+'_met.csv')
            
            # export county-level meteorology data 
            with open(metname,'wb') as f:
                cursor.execute("SELECT * FROM {MOVES_database}.zonemonthhour WHERE {MOVES_database}.zonemonthhour.zoneID = {zoneID}".format(**kvals))    
                csv_writer = csv.writer(f)
                csv_writer.writerow([i[0] for i in cursor.description]) # write headers
                csv_writer.writerows(cursor)
            
        cursor.close()
                
    def createNationalData(self):
        """
        Create national data for MOVES, including: 
            Alternate Vehicle Fuels & Technologies (avft)
            average speed distribution
            age distribution (currently only works for 2015,2017,2022,and 2040)
            day VMT fraction
            month VMT fraction
            hour VMT fraction
            road type fraction 
        """
        logger.info('Creating national data files for MOVES')      
        
        # connect to MOVES database
        connection = pymysql.connect(host=self.MOVES_db_host, user=self.MOVES_db_user,password=self.MOVES_db_pass,db=self.MOVES_database)
        cursor = connection.cursor()

        # initialize kvals for string formatting 
        kvals ={}
        kvals['year']=self.yr
        kvals['MOVES_database']=self.MOVES_database
            
        # export MOVES defaults for national inputs (i.e., hourVMTFraction, monthVMTFraction, dayVMTFraction, and avgspeeddistribution)
        tablelist = ['hourvmtfraction','monthvmtfraction','dayvmtfraction','avgspeeddistribution']
        for table in tablelist:
            kvals['table']=table
            filename = os.path.join(self.save_path_nationalinputs, table+'.csv')
            cursor.execute("SELECT * FROM {MOVES_database}.{table} WHERE sourceTypeID = '61';".format(**kvals))
            
            with open(filename, "wb") as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow([i[0] for i in cursor.description]) # write headers
                csv_writer.writerows(cursor)
        
        agedistname = os.path.join(self.save_path_nationalinputs, 'default-age-distribution-tool-moves'+self.yr+'.csv')
        with open(agedistname,'wb') as f: 
            csv_writer = csv.writer(f)
            csv_writer.writerow(['sourceTypeID','yearID','ageID','ageFraction'])
            for bins in range(0,31): 
                csv_writer.writerow(['61', self.yr, bins, self.age_distribution[self.yr][bins]])
            
    def createBatchfiles(self):
        """
        Create batch files for importing data using MOVES county data manager and running MOVES  
        """
        logger.info('Creating batch files for MOVES runs')        
        
        # loop through FIPS codes
        for FIPS in self.FIPSlist:
            # instantiate MOVESBatch
            batchfile = MB.MOVESBatch(crop=self.crop, model_run_title=self.model_run_title,FIPS=FIPS,yr=self.yr,path_MOVES=self.path_MOVES,save_path_importfiles=self.save_path_importfiles,save_path_runspecfiles=self.save_path_runspecfiles)
            # create MOVES batch import file            
            batchfile.create_MOVES_batchimport()
            # create MOVES batch run file
            batchfile.create_MOVES_batchrun()
            
    def createXMLimport(self):
        """
        Create XML files for importing data using MOVES county data manager
        """
        logger.info('Creating XML files for importing MOVES data')
        
        # filepaths for national MOVES defaults 
        # @TODO: replace filepaths with database queries that export csv or text files? or put hardcoded values into python classes that generate text files?   
        save_path_nat_inputs = "C:\MOVESdata\National_Inputs"
        agefilename = os.path.join(save_path_nat_inputs, "default-age-distribution-tool-moves"+self.yr+".txt")
        speedfilename = os.path.join(save_path_nat_inputs,"speed_default.txt")
        fuelsupfilename = os.path.join(save_path_nat_inputs,"fuel_default.txt")
        fuelformfilename = os.path.join(save_path_nat_inputs,"fuel_default_FuelFormulation.txt")
        fuelusagefilename = os.path.join(save_path_nat_inputs,"fuel_default_FuelUsageFraction.txt")
        avftfilename = os.path.join(save_path_nat_inputs,"fuel_default_avft.txt")
        roadtypefilename = os.path.join(save_path_nat_inputs,"roadtype_temp.txt")
        monthVMTfilename = os.path.join(save_path_nat_inputs,"MonthVMTFraction")
        dayVMTfilename = os.path.join(save_path_nat_inputs,"DayVMTFraction")
        hourVMTfilename = os.path.join(save_path_nat_inputs,"HourVMTFraction")
        
        #meteorology data changes later (dummy file later dropped from database and correct county imported)
        metfilename = os.path.join(save_path_nat_inputs,"met_default.txt")
              
        # loop through FIPS codes 
        for FIPS in self.FIPSlist:
            # create import filename using FIPS code, crop, and scenario year 
            im_filename = os.path.join(self.save_path_importfiles, FIPS+"_import_"+self.yr+'_'+self.crop+".mrs")
            # create filename for sourcetype input file using FIPS code, crop, and scenario year 
            sourcetypefilename = os.path.join(self.save_path_countyinputs, FIPS + "_sourcetype_"+self.yr+'_'+self.crop+".csv")
            # create filename for VMT input file using FIPS code, crop, and scenario year 
            VMTfilename = os.path.join(self.save_path_countyinputs, FIPS + "_vehiclemiletraveled_"+self.yr+'_'+self.crop+".csv")
            # instantiate GenerateMOVESImport class 
            xmlimport = GenMOVESIm.GenerateMOVESImport(crop=self.crop,FIPS=FIPS, yr=self.yr, MOVES_timespan=self.MOVES_timespan, agefilename=agefilename,speedfilename=speedfilename,fuelsupfilename=fuelsupfilename,fuelformfilename=fuelformfilename,fuelusagefilename=fuelusagefilename,avftfilename=avftfilename,metfilename=metfilename,roadtypefilename=roadtypefilename,sourcetypefilename=sourcetypefilename,VMTfilename=VMTfilename,monthVMTfilename=monthVMTfilename,dayVMTfilename=dayVMTfilename,hourVMTfilename=hourVMTfilename)
            # execute function for creating XML import file             
            xmlimport.create_import_file(im_filename)
            
    def createXMLrunspec(self):
        """
        Create XML file for running MOVES
        """
        logger.info('Creating XML files for running MOVES')
        
        # loop through FIPS codes 
        for FIPS in self.FIPSlist:
            # create filename for runspec file using FIPS code, crop, and scenario year
            run_filename = os.path.join(self.save_path_runspecfiles, FIPS+"_runspec_"+self.yr+'_'+self.crop+".mrs") 
            # instantiate GenerateMOVESRunspec class
            xmlrunspec = GenMOVESRun.GenerateMOVESRunspec(crop=self.crop,FIPS=FIPS,yr=self.yr, MOVES_timespan=self.MOVES_timespan,server=self.MOVES_db_host)
            # execute function for creating XML file             
            xmlrunspec.create_runspec_files(run_filename)
    
    def importdata(self): 
        """
        Import MOVES data into MySQL database 
        """
        logger.info('Importing MOVES files')  
        
        # path for import batch file
        self.importbatch = os.path.join(self.path_MOVES, 'batch_import_FPEAM_' + self.model_run_title +'.bat')
       
        # exectute batch file and log output 
        # @TODO: replace hardcoded values with string (for some reason string version doesn't work correctly)
        output= subprocess.Popen(r"C:\Users\Public\EPA\MOVES\MOVES2014a\batch_import_FPEAM_aelocal.bat",cwd=self.path_MOVES,stdout=subprocess.PIPE).stdout.read()
        logger.debug('MOVES output: %s' % output)
        