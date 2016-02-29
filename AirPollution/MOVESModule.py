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
        
        # get information from config file 
        self.model_run_title = config.get('title') # scenario title 
        self.MOVES_database = config.get('MOVES_database') # MOVES database name 
        self.MOVES_db_user = config.get('MOVES_db_user') # username for MOVES database
        self.MOVES_db_pass = config.get('MOVES_db_pass') # password for MOVES database
        self.MOVES_db_host = config.get('MOVES_db_host') # host for MOVES database
        self.MOVES_timespan = config.get('MOVES_timespan') # timespan for MOVES runs
        self.age_distribution = config.get('age_distribution') # age distribution dictionary for MOVES runs (varies by scenario year)
        self.VMT_fraction = config.get('VMT_fraction') # fraction of VMT by road type 
        self.fuelfraction = config.get('fuel_fraction') # fuel fraction 

        
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
            fuelsupplyname = os.path.join(self.save_path_countyinputs, FIPS+'_fuelsupply_'+self.yr+'.csv')
            fuelformname = os.path.join(self.save_path_countyinputs, FIPS+'_fuelformulation_'+self.yr+'.csv')
            fuelusagename = os.path.join(self.save_path_countyinputs, FIPS+'_fuelusagefraction_'+self.yr+'.csv')
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
        
        # create file for alternative vehicle fuels and technology (avft)

        sourcetype = '61'
        engtech = '1'
        avftname = os.path.join(self.save_path_nationalinputs, 'avft.csv')
        with open(avftname, "wb") as f:
             csv_writer = csv.writer(f)
             csv_writer.writerow(['sourceTypeID','modelYearID','fuelTypeID','engTechID','fuelEngFraction']) # write headers
             i = 0
             for modelyear in range(1960,2051):
                for fueltype in range(1,3):
                    csv_writer.writerow([sourcetype,modelyear,fueltype,engtech,self.fuelfraction[i]])
                    i = i+1
       
        # create file for default age distribution (values in age_distribution dictionary were computed using MOVES Default Age Distribution Tool)
        agedistname = os.path.join(self.save_path_nationalinputs, 'default-age-distribution-tool-moves'+self.yr+'.csv')
        with open(agedistname,'wb') as f: 
            csv_writer = csv.writer(f)
            csv_writer.writerow(['sourceTypeID','yearID','ageID','ageFraction'])
            for bins in range(0,31): 
                csv_writer.writerow(['61', self.yr, bins, self.age_distribution[self.yr][bins]])
        
        # create file for road type fraction 
        roadtypename = os.path.join(self.save_path_nationalinputs, 'roadtype.csv')
        with open(roadtypename,'wb') as f: 
            csv_writer = csv.writer(f)
            csv_writer.writerow(['sourceTypeID','roadTypeID','roadTypeVMTFraction'])
            for roadtype in range(2,6):
                csv_writer.writerow(['61', roadtype,self.VMT_fraction[str(roadtype)]])
            
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
            im_filename = batchfile.create_MOVES_batchimport()
            # create MOVES batch run file
            run_filename = batchfile.create_MOVES_batchrun()
        return run_filename, im_filename
        
    def createXMLimport(self):
        """
        Create XML files for importing data using MOVES county data manager
        """
        logger.info('Creating XML files for importing MOVES data')
        
        # filepaths for national MOVES defaults 
        agefilename = os.path.join(self.save_path_nationalinputs, "default-age-distribution-tool-moves"+self.yr+".csv")
        speedfilename = os.path.join(self.save_path_nationalinputs,"avgspeeddistribution.csv")
        avftfilename = os.path.join(self.save_path_nationalinputs,"avft.csv")
        roadtypefilename = os.path.join(self.save_path_nationalinputs,"roadtype.csv")
        monthVMTfilename = os.path.join(self.save_path_nationalinputs,"monthvmtfraction.csv")
        dayVMTfilename = os.path.join(self.save_path_nationalinputs,"dayvmtfraction.csv")
        hourVMTfilename = os.path.join(self.save_path_nationalinputs,"hourvmtfraction.csv")
        
        # loop through FIPS codes 
        for FIPS in self.FIPSlist:
            # filepaths for county-level input files 
            metfilename = os.path.join(self.save_path_countyinputs,FIPS+'_met.csv')
            fuelsupfilename = os.path.join(self.save_path_countyinputs, FIPS+'_fuelsupply_'+self.yr+'.csv')
            fuelformfilename = os.path.join(self.save_path_countyinputs,FIPS+'_fuelformulation_'+self.yr+'.csv')
            fuelusagefilename = os.path.join(self.save_path_countyinputs,FIPS+'_fuelusagefraction_'+self.yr+'.csv')  
            sourcetypename = os.path.join(self.save_path_countyinputs, FIPS + "_sourcetype_"+self.yr+'_'+self.crop+".csv")
            vmtname = os.path.join(self.save_path_countyinputs, FIPS + "_vehiclemiletraveled_"+self.yr+'_'+self.crop+".csv")
            
            # create import filename using FIPS code, crop, and scenario year 
            im_filename = os.path.join(self.save_path_importfiles, FIPS+"_import_"+self.yr+'_'+self.crop+".mrs")
            # instantiate GenerateMOVESImport class 
            xmlimport = GenMOVESIm.GenerateMOVESImport(crop=self.crop,FIPS=FIPS, yr=self.yr, MOVES_timespan=self.MOVES_timespan, agefilename=agefilename,speedfilename=speedfilename,fuelsupfilename=fuelsupfilename,fuelformfilename=fuelformfilename,fuelusagefilename=fuelusagefilename,avftfilename=avftfilename,metfilename=metfilename,roadtypefilename=roadtypefilename,sourcetypefilename=sourcetypename,VMTfilename=vmtname,monthVMTfilename=monthVMTfilename,dayVMTfilename=dayVMTfilename,hourVMTfilename=hourVMTfilename)
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
    
    def importdata(self,filename): 
        """
        Import MOVES data into MySQL database 
        """
        logger.info('Importing MOVES files')  
        
        # exectute batch file and log output 
        output= subprocess.Popen(filename,cwd=self.path_MOVES,stdout=subprocess.PIPE).stdout.read()
        logger.debug('MOVES output: %s' % output)
        