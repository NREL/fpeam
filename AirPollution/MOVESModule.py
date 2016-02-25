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

class MOVESModule(): 
    "generates XML files for import and runspec files and creates batch files for importing and running MOVES"
    
    def __init__(self,crop,FIPSlist,yr,path_MOVES,save_path_importfiles,save_path_runspecfiles,save_path_countyinputs,server): 
        self.crop = crop        
        self.FIPSlist = FIPSlist
        self.yr = yr
        self.path_MOVES = path_MOVES
        self.save_path_importfiles = save_path_importfiles
        self.save_path_runspecfiles = save_path_runspecfiles   
        self.save_path_countyinputs = save_path_countyinputs
        self.server = server
        self.model_run_title = config.get('title')
        self.moves_path = config.get('moves_path')
        
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
            xmlrunspec = GenMOVESRun.GenerateMOVESRunspec(crop=self.crop,FIPS=FIPS,yr=self.yr, months=mo, days=d,beginhour=bhr, endhour=ehr,server=self.server)
            xmlrunspec.create_runspec_files(run_filename)
    
    def importdata(self): 

        # master path to the batch file that keeps track of all the run_code batch files.
        logger.debug('Importing MOVES files')        
        self.importbatch = os.path.join(self.moves_path, 'batch_import_FPEAM_' + self.model_run_title +'.bat')
       
        output= subprocess.Popen(r"C:\Users\Public\EPA\MOVES\MOVES2014a\batch_import_FPEAM_aelocal.bat",cwd="C:\Users\Public\EPA\MOVES\MOVES2014a",stdout=subprocess.PIPE).stdout.read()
        logger.debug('Moves output: %s' % output)
