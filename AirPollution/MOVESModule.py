# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 11:00:20 2016

Generates XML files for importing data and running MOVES
Also creates batch files for executing MOVES imports and runs 

Inputs include: 
    year of scenario
    FIPS code
    path to MOVES (where batch files are saved for execution)
    path to XML import files
    path to XML runspec files

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
    "generates XML files for import and runspec files and creates batch files for importing and running MOVES"
    
    def __init__(self,crop,FIPSlist,yr,path_MOVES,save_path_importfiles,save_path_runspecfiles,save_path_countyinputs): 
        self.crop = crop        
        self.FIPSlist = FIPSlist
        self.yr = yr
        self.path_MOVES = path_MOVES
        self.save_path_importfiles = save_path_importfiles
        self.save_path_runspecfiles = save_path_runspecfiles   
        self.save_path_countyinputs = save_path_countyinputs
        self.model_run_title = config.get('title')
        self.MOVES_database = config.get('MOVES_database')
        self.MOVES_db_user = config.get('MOVES_db_user')
        self.MOVES_db_pass = config.get('MOVES_db_pass')
        self.MOVES_db_host = config.get('MOVES_db_host')
        
    def createcountydata(self):
                #required inputs 
        for FIPS in self.FIPSlist:         
            
            # @TODO: replace vmt_shorthaul with database query to calculate county-level vehicle populations (need to import data first)
            vmt_shorthaul = 10000 #annual vehicle miles traveled by combination short-haul trucks
            
            pop_shorthaul = 1 #population of combination short-haul trucks (assume one per trip and only run MOVES for single trip)
                    
            #county-level input files for MOVES 
            vmtname = os.path.join(self.save_path_countyinputs, FIPS+'_vehiclemiletraveled_'+self.yr+'_'+self.crop+'.csv')
            sourcetypename = os.path.join(self.save_path_countyinputs, FIPS+'_sourcetype_'+self.yr+'_'+self.crop+'.csv')
            
            #annual vehicle miles traveled by vehicle type 
            with open(vmtname,'wb') as csvfile:
                vmtwriter = csv.writer(csvfile, dialect='excel')
                vmtwriter.writerow(['HPMSVtypeID', 'yearID', 'HPMSBaseYearVMT'])
                vmtwriter.writerow(['60', self.yr, vmt_shorthaul]) #combination short-haul truck
            
            #source type population (number of vehicles by vehicle type)
            with open(sourcetypename,'wb') as csvfile:
                popwriter = csv.writer(csvfile, dialect='excel')
                popwriter.writerow(['yearID', 'sourceTypeID', 'sourceTypePopulation'])
                popwriter.writerow([self.yr,"61", pop_shorthaul]) #combination short-haul truck
    
    def createBatchfiles(self, model_run_title):
                
        for FIPS in self.FIPSlist:
            batchfile = MB.MOVESBatch(run_code = self.crop, model_run_title=model_run_title,FIPS=FIPS,yr=self.yr,path_MOVES=self.path_MOVES,save_path_importfiles=self.save_path_importfiles,save_path_runspecfiles=self.save_path_runspecfiles)
            batchfile.create_MOVES_batchimport()
            batchfile.create_MOVES_batchrun()
            
    def createXMLimport(self,mo,bhr,ehr,d, save_path_import):
        
        #filepaths for national MOVES defaults 
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
        
        #filepaths for county-level data (i.e., source type popluation and vehicle miles travele) 
        save_path_county_inputs = self.save_path_countyinputs

        
        for FIPS in self.FIPSlist:
            im_filename = os.path.join(save_path_import, FIPS+"_import_"+self.yr+'_'+self.crop+".mrs")
            sourcetypefilename = os.path.join(save_path_county_inputs, FIPS + "_sourcetype_"+self.yr+'_'+self.crop+".csv")
            VMTfilename = os.path.join(save_path_county_inputs, FIPS + "_vehiclemiletraveled_"+self.yr+'_'+self.crop+".csv")
            xmlimport = GenMOVESIm.GenerateMOVESImport(crop=self.crop,FIPS=FIPS, yr=self.yr, months=mo, days=d,beginhour=bhr, endhour=ehr, agefilename=agefilename,speedfilename=speedfilename,fuelsupfilename=fuelsupfilename,fuelformfilename=fuelformfilename,fuelusagefilename=fuelusagefilename,avftfilename=avftfilename,metfilename=metfilename,roadtypefilename=roadtypefilename,sourcetypefilename=sourcetypefilename,VMTfilename=VMTfilename,monthVMTfilename=monthVMTfilename,dayVMTfilename=dayVMTfilename,hourVMTfilename=hourVMTfilename)
            xmlimport.create_import_file(im_filename)
            
    def createXMLrunspec(self,mo,bhr,ehr,d, save_path_runspec):
        for FIPS in self.FIPSlist:
            run_filename = os.path.join(save_path_runspec, FIPS+"_runspec_"+self.yr+'_'+self.crop+".mrs") 
            xmlrunspec = GenMOVESRun.GenerateMOVESRunspec(crop=self.crop,FIPS=FIPS,yr=self.yr, months=mo, days=d,beginhour=bhr, endhour=ehr,server=self.MOVES_db_host)
            xmlrunspec.create_runspec_files(run_filename)
    
    def importdata(self): 

        logger.debug('Importing MOVES files')        
        # path for import batch file
        self.importbatch = os.path.join(self.path_MOVES, 'batch_import_FPEAM_' + self.model_run_title +'.bat')
       
        # exectute batch file and log output 
        # @TODO: replace hardcoded values with string
        output= subprocess.Popen(r"C:\Users\Public\EPA\MOVES\MOVES2014a\batch_import_FPEAM_aelocal.bat",cwd=self.path_MOVES,stdout=subprocess.PIPE).stdout.read()
        logger.debug('MOVES output: %s' % output)

        # modify meteoroology and fuel data using default values in MOVES database         
        logger.debug('Modifying meteorology and fuel data')        
        kvals = {}
        kvals['MOVES_database']=self.MOVES_database        
        
        connection = pymysql.connect(host=self.MOVES_db_host, user=self.MOVES_db_user,password=self.MOVES_db_pass,db=self.MOVES_database)
        cursor = connection.cursor()
        
        query = ''
        for FIPS in self.FIPSlist: 
            kvals['year'] = self.yr
            kvals['countyID'] = FIPS
            kvals['zoneID'] = FIPS + '0'        
            kvals['county_db'] = 'fips_' + FIPS + '_' + self.crop + '_in'  
            query = query + (("""DROP TABLE IF EXISTS {county_db}.zonemonthhour;
                    DROP TABLE IF EXISTS {county_db}.fuelsupply;
                    DROP TABLE IF EXISTS {county_db}.fuelformulation;
                    DROP TABLE IF EXISTS {county_db}.fuelusagefraction;
                    
                    CREATE TABLE {county_db}.zonemonthhour
                    AS (SELECT * FROM {MOVES_database}.zonemonthhour 
                    WHERE {MOVES_database}.zonemonthhour.zoneID = {zoneID});
                    
                    CREATE TABLE {county_db}.fuelsupply
                    AS (SELECT * FROM {MOVES_database}.fuelsupply
                    WHERE {MOVES_database}.fuelsupply.fuelRegionID =
                    (SELECT regionID FROM {MOVES_database}.regioncounty WHERE countyID = '{countyID}' AND fuelYearID='{year}')
                    AND {MOVES_database}.fuelsupply.fuelYearID = '{year}'
                    AND {MOVES_database}.fuelsupply.fuelFormulationID = '25005');
                    
                    CREATE TABLE {county_db}.fuelformulation
                    AS (SELECT * FROM {MOVES_database}.fuelformulation
                    WHERE {MOVES_database}.fuelformulation.fuelSubtypeID = '21' OR {MOVES_database}.fuelformulation.fuelSubtypeID = '20');
                    
                    
                    CREATE TABLE {county_db}.fuelusagefraction
                    AS (SELECT * FROM {MOVES_database}.fuelusagefraction
                    WHERE {MOVES_database}.fuelusagefraction.countyID='{countyID}' 
                    AND {MOVES_database}.fuelusagefraction.fuelYearID = '{year}'
                    AND {MOVES_database}.fuelusagefraction.fuelSupplyFuelTypeID = '2');
                    """).format(**kvals))
        
        cursor.execute(query)
        connection.commit()
        