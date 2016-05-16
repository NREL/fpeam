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
import time


class MOVESBatch:
    """
    Generate batch files for 1) importing data using MOVES County Data Manager and 2) running MOVES
    """ 
    
    def __init__(self, crop, model_run_title, fips, yr, path_moves, save_path_importfiles, save_path_runspecfiles):
        # get timestamp for run
        t = time.localtime()
        timestamp = time.strftime('_%b-%d-%Y_%H%M', t)

        self.crop = crop  # crop name
        self.model_run_title = model_run_title  # scenario name
        self.path_moves = path_moves
        self.save_path_importfiles = save_path_importfiles
        self.save_path_runspecfiles = save_path_runspecfiles
        self.setenv_file = os.path.join(self.path_moves, 'setenv.bat')

        # initialize kvals dictionary for string formatting
        kvals = dict()
        kvals['yr'] = yr  # scenario year
        kvals['crop'] = crop  # crop type
        kvals['title'] = model_run_title  # scenario name
        kvals['timestamp'] = timestamp  # timestamp of run
        kvals['fips'] = fips  # FIPS code
        # @TODO: change filepath so these don't write to the MOVES root folder (should go to the scenario or project folder)
        self.importbatch = os.path.join(path_moves, 'batch_import_FPEAM_{fips}_{yr}_{crop}_{title}{timestamp}.bat'.format(**kvals))  # path for batch import file
        self.importfilename = os.path.join(save_path_importfiles, '{fips}_import_{yr}_{crop}.mrs'.format(**kvals))  # path for XML import files
        self.runbatch = os.path.join(path_moves, 'batch_run_FPEAM_{fips}_{yr}_{crop}_{title}{timestamp}.bat'.format(**kvals))  # path for batch run file
        self.runfilename = os.path.join(save_path_runspecfiles, '{fips}_runspec_{yr}_{crop}.mrs'.format(**kvals))  # path for XML runspec files
        self.fips = fips  # FIPS code
        self.yr = yr  # scenario year
        
    def create_moves_batch_import(self):
        """
        Create batch file for importing data using MOVES County Data Manager
        """
        # append import files to batch import file
        with open(self.importbatch, 'a') as csvfile:
            batchwriter = csv.writer(csvfile)
            batchwriter.writerow([self.setenv_file])
            batchwriter.writerow(['echo Running %s' % (os.path.join(self.save_path_importfiles, '{fips}_import_{yr}_{crop}.mrs'.format(fips=self.fips, yr=self.yr, crop=self.crop)))])  # @TODO: remove this echo and make a logger call
            batchwriter.writerow(['java -Xmx512M gov.epa.otaq.moves.master.commandline.MOVESCommandLine -i {importfile}'.format(importfile=self.importfilename)])
        return self.importbatch
        
    def create_moves_batch_run(self):
        """
        Create batch file for running MOVES
        """
        # append import files to batch run file
        with open(self.runbatch, 'a') as csvfile:
            batchwriter = csv.writer(csvfile)
            batchwriter.writerow([self.setenv_file])
            batchwriter.writerow(['echo Running %s' % (os.path.join(self.save_path_runspecfiles, '{fips}_runspec_{yr}_{crop}.mrs'.format(fips=self.fips, yr=self.yr, crop=self.crop)))])  # @TODO: remove this echo and make a logger call
            batchwriter.writerow(['java -Xmx512M gov.epa.otaq.moves.master.commandline.MOVESCommandLine -r {runfile}'.format(runfile=self.runfilename)])
        return self.runbatch
