# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 13:21:58 2016

Generates batch files for importing data and running MOVES

Inputs include: 
    crop name   
    title of scenario
    FIPS code
    year of scenario
    path to MOVES (where batch files are saved for execution)
    path to XML import files
    path to XML runspec files
    
Result: 
    two batch files ("batch_import.bat" and "batch_run.bat") generated in MOVES folder
    
@author: aeberle
"""
import csv
import os 

class MOVESBatch:
    """
    Generate batch files for 1) importing data using MOVES County Data Manager and 2) running MOVES
    """ 
    
    def __init__(self,crop,model_run_title,FIPS,yr,path_MOVES,save_path_importfiles,save_path_runspecfiles):
        self.crop = crop # crop name
        self.model_run_title = model_run_title # scenario name
        self.importbatch = os.path.join(path_MOVES, 'batch_import_FPEAM_' + self.model_run_title +'.bat') # path for batch import file
        self.importfilename = os.path.join(save_path_importfiles, FIPS+"_import_"+yr+'_'+self.crop+".mrs") # path for XML import files 
        self.runbatch = os.path.join(path_MOVES, 'batch_run_FPEAM_' + self.model_run_title +'.bat') # path for batch run file
        self.runfilename = os.path.join(save_path_runspecfiles, FIPS+"_runspec_"+yr+'_'+self.crop+".mrs") # path for XML runspec files
        self.FIPS = FIPS # FIPS code
        self.yr = yr # scenario year
        
    def create_MOVES_batchimport(self):
        """
        Create batch file for importing data using MOVES County Data Manager
        """
        # append import files to batch import file
        with open(self.importbatch,'a') as csvfile:
            batchwriter = csv.writer(csvfile)
            batchwriter.writerow(['echo Running ' + self.FIPS + '_import_' + self.yr +'_'+self.crop+'.mrs'])
            batchwriter.writerow(['java -Xmx512M gov.epa.otaq.moves.master.commandline.MOVESCommandLine -i ' + self.importfilename]) 
        
    def create_MOVES_batchrun(self):
        """
        Create batch file for running MOVES
        """
        # append import files to batch run file
        with open(self.runbatch,'a') as csvfile:
            batchwriter = csv.writer(csvfile)
            batchwriter.writerow(['echo Running ' + self.FIPS + '_runspec_' + self.yr +'_'+self.crop+'.mrs'])
            batchwriter.writerow(['java -Xmx512M gov.epa.otaq.moves.master.commandline.MOVESCommandLine -r ' + self.runfilename]) 
    