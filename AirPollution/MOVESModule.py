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

class MOVESModule(): 
    "generates XML files for import and runspec files and creates batch files for importing and running MOVES"
    
    def __init__(self,FIPSlist,yr,path_MOVES,save_path_importfiles,save_path_runspecfiles,server): 
        self.FIPSlist = FIPSlist
        self.yr = yr
        self.path_MOVES = path_MOVES
        self.save_path_importfiles = save_path_importfiles
        self.save_path_runspecfiles = save_path_runspecfiles    
        self.server = server
        
        #check to make sure batch files don't already exist
        self.importbatch = os.path.join(path_MOVES, 'batch_import.bat')
        try:
            os.remove(self.importbatch)
        except OSError:
            pass
        
        self.runbatch = os.path.join(path_MOVES, 'batch_run.bat')
        try:
            os.remove(self.runbatch)
        except OSError:
            pass

        
    def createBatchfiles(self):
                
        for FIPS in self.FIPSlist:
            batchfile = MB.MOVESBatch(FIPS=FIPS,yr=self.yr,path_MOVES=self.path_MOVES,save_path_importfiles=self.save_path_importfiles,save_path_runspecfiles=self.save_path_runspecfiles)
            batchfile.create_MOVES_batch()
            
    def createXMLimport(self,mo,bhr,ehr,d, save_path_import):
        
        #filepaths for national MOVES defaults 
        save_path_nat_inputs = "C:/MOVES/National_Inputs/"
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
        save_path_county_inputs = "C:/MOVES/County_Inputs/"

        
        for FIPS in self.FIPSlist:
            im_filename = os.path.join(save_path_import, FIPS+"_import_"+self.yr+".mrs")
            sourcetypefilename = os.path.join(save_path_county_inputs, FIPS + "_sourcetype_"+self.yr+".csv")
            VMTfilename = os.path.join(save_path_county_inputs, FIPS + "_vehiclemiletraveled_"+self.yr+".csv")
            xmlimport = GenMOVESIm.GenerateMOVESImport(FIPS=FIPS, yr=self.yr, months=mo, days=d,beginhour=bhr, endhour=ehr, agefilename=agefilename,speedfilename=speedfilename,fuelsupfilename=fuelsupfilename,fuelformfilename=fuelformfilename,fuelusagefilename=fuelusagefilename,avftfilename=avftfilename,metfilename=metfilename,roadtypefilename=roadtypefilename,sourcetypefilename=sourcetypefilename,VMTfilename=VMTfilename,monthVMTfilename=monthVMTfilename,dayVMTfilename=dayVMTfilename,hourVMTfilename=hourVMTfilename)
            xmlimport.create_import_file(im_filename)
            
    def createXMLrunspec(self,mo,bhr,ehr,d, save_path_runspec):
        for FIPS in self.FIPSlist:
            run_filename = os.path.join(save_path_runspec, FIPS+"_runspec_"+self.yr+".mrs") 
            xmlrunspec = GenMOVESRun.GenerateMOVESRunspec(FIPS=FIPS,yr=self.yr, months=mo, days=d,beginhour=bhr, endhour=ehr,server=self.server)
            xmlrunspec.create_runspec_files(run_filename)
        