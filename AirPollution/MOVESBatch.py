# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 13:21:58 2016

Generates batch files for importing data and running MOVES

Inputs include: 
    year of scenario
    FIPS code
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
    "generate batch file for MOVES" 
    
    def __init__(self,FIPS,yr,path_MOVES,save_path_importfiles,save_path_runspecfiles):
        #county-level input files for MOVES 
        self.importbatch = os.path.join(path_MOVES, 'batch_import.bat')
        self.importfilename = os.path.join(save_path_importfiles, FIPS+"_import_"+yr+".mrs") 
        #county-level input files for MOVES 
        self.runbatch = os.path.join(path_MOVES, 'batch_run.bat')
        self.runfilename = os.path.join(save_path_runspecfiles, FIPS+"_runspec_"+yr+".mrs") 
        self.FIPS = FIPS
        self.yr = yr
        
    def create_MOVES_batchimport(self):

        #create batch import file
        with open(self.importbatch,'a') as csvfile:
            batchwriter = csv.writer(csvfile)
            batchwriter.writerow(['echo Running ' + self.FIPS + '_import_' + self.yr +'.mrs'])
            batchwriter.writerow(['java -Xmx512M gov.epa.otaq.moves.master.commandline.MOVESCommandLine -i ' + self.importfilename]) 

    def create_MOVES_batchrun(self):

        #create batch run file
        with open(self.runbatch,'a') as csvfile:
            batchwriter = csv.writer(csvfile)
            batchwriter.writerow(['echo Running ' + self.FIPS + '_runspec_' + self.yr +'.mrs'])
            batchwriter.writerow(['java -Xmx512M gov.epa.otaq.moves.master.commandline.MOVESCommandLine -r ' + self.runfilename]) 
    
    def create_MOVES_batch(self):
        self.create_MOVES_batchimport        
        self.create_MOVES_batchrun
        
