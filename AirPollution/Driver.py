import Container
import Batch
from model.Database import Database
import QueryRecorder as qr
from PyQt4 import QtCore

import Options as Opt
import Allocate as Alo
import Population as Pop
import UpdateDatabase
import FugitiveDust
import Chemical
import CombustionEmissions 
import Fertilizer
import SinglePassAllocation 
import NEIComparison
import EmissionsPerGalFigure
from EmissionsPerAcreFigure import EmissionsPerAcreFigure
from EmissionPerProdFigure import EmissionPerProdFigure
import RatioToNEIFigure
import ContributionFigure

'''
Drives program.
Global Variables: modelRunTitle, run_codes, path, db, qr.
All stored in a Container.
Temporary Global Variables: run_code, fips, state, episodeYear.
'''
class Driver:
    
    '''
    Save important variables for the running of the program.
    @param modelRunTitle: Scenario title.
    @param run_codes: Run codes to keep track of where you are in the program  
    '''
    def __init__(self, _modelRunTitle, run_codes, _db):
        # add run title.
        self.modelRunTitle = self._addTitle(_modelRunTitle)
        # add run codes.
        self.run_codes = run_codes
        # container to pass info around.
        self.cont = Container.Container()
        self.cont.set('modelRunTitle', self._addTitle(_modelRunTitle))
        self.cont.set('run_codes', run_codes)
        self.cont.set('path', 'C:/Nonroad/%s/' % (_modelRunTitle))
        self.cont.set('db', _db)
        self.cont.set('qr', qr.QueryRecorder(self.cont.get('path')))
        # create Batch runner.
        self.batch = Batch.Batch(self.cont)
    
    '''
    Make sure the program is less then 8 characters.
    Is not a run code.
    @param title: Title of the program.
    '''
    def _addTitle(self, title):
        assert len(title) <= 8
        return title
        
    '''
    Set up the NONROAD program by creating option, allocation, and population files.
    Also creates batch files to run.
    TODO: maybe should make episodeYear to be a global variable in this class instead of Options.
    '''    
    def setupNONROAD(self):
        #initialize objects
        scenario = Opt.ScenarioOptions(self.cont)
        alo = Alo.Allocate(self.cont)
        # create batch file.
        self.batch.getMaster('w')
                
        # go to each run code.
        for run_code in self.run_codes:
            
            print run_code
            #query database for appropriate production data based on run_code:
            # fips, state, productions 
            # TODO: should this return the data? And pass the data as a variable in Driver?
            scenario.getData(run_code)
               
            #initialize variables
            state = scenario.data[0][1]
            fips_prior = str(scenario.data[0][0])
            
            #New population object created for each run_code  
            # Pop is the abstract class and .<type> is the concrete class.  
            if run_code.startswith('CG_I'): pop = Pop.CornGrainIrrigationPop(self.cont, scenario.episodeYear, run_code)
            elif run_code.startswith('SG'): pop = Pop.SwitchgrassPop(self.cont, scenario.episodeYear, run_code)
            elif run_code.startswith('FR'): pop = Pop.ForestPop(self.cont, scenario.episodeYear, run_code)
            elif run_code.startswith('CS'): pop = Pop.ResiduePop(self.cont, scenario.episodeYear, run_code)
            elif run_code.startswith('WS'): pop = Pop.ResiduePop(self.cont, scenario.episodeYear, run_code)    
            elif run_code.startswith('CG'): pop = Pop.CornGrainPop(self.cont, scenario.episodeYear, run_code)
            
            # is it possible to instantiate new classes each time?
            alo.initializeAloFile(state, run_code, scenario.episodeYear)
            pop.initializePop(scenario.data[0])
            self.batch.initialize(run_code)
            
            # go through each row of the data table.
            for dat in scenario.data:
                fips = str(dat[0])
                '''
                The db table is ordered alphabetically.
                The search will look through a state. When the state changes in the table,
                then the loop will go to the else, closing the old files. and initializing new files.
                '''  
                # dat[1] is the state.            
                if dat[1] == state:
                    # indicator is harvested acres. Except for FR when it is produce.
                    indicator = dat[2]
                    alo.writeIndicator(fips, indicator)
                    pop.append_Pop(fips, dat)
                # last time through a state, will close different files, and start new ones.
                else:
                    #write *.opt file, close allocation file, close *.pop file            
                    Opt.NROptionFile(self.cont, state, fips_prior, run_code, scenario.episodeYear)
                    alo.writeSumAndClose(fips_prior)
                    pop.finishPop()
                    self.batch.append(state, run_code)
                            
                    fips_prior = fips
                    state = dat[1]   
        
                    #initialize new pop and allocation files.                      
                    alo.initializeAloFile(state, run_code, scenario.episodeYear)
                    pop.initializePop(dat)
                    # indicator is harvested acres. Except for FR when it is produce.
                    indicator = dat[2]
                    alo.writeIndicator(fips, indicator)
                    pop.append_Pop(fips, dat)            
                 
            #close allocation files    
            Opt.NROptionFile(self.cont, state, fips_prior, run_code, scenario.episodeYear)        
            alo.writeSumAndClose(fips_prior)
            pop.finishPop()
            self.batch.append(state, run_code)
            self.batch.finish(run_code)
        
        #close scenariobatchfile
        self.batch.scenarioBatchFile.close()
        # save path for running batch files.
        # why is this here?
        self.path = scenario.path
     
    '''
    Run the NONROAD program by opening the batch files.
    @param qprocess: sub process controller from the Controller.
    Used to control the flow of the NONROAD program within the application.
    '''   
    def runNONROAD(self, qprocess):
        self.batch.run(qprocess) 
        
    '''
    Create and populate the schema with the emissions inventory.  
    @param fertFeed: Dictionary containing each feedstock and weather to do fertilizer calculations. 
    dict(boolean)
    @param fertDist: The five numbers must add to 1 b/c they represent the percentage of
    each of the five fertilizers used. list(float)  
    @param pestFeed: Weather a feedstock should calculate the pesticides used. A dictionary of
    feedstocks to what to do. dict(boolean)
    @param operationDict: Dictionary containing each feedstock. Each feedstock contains a dictionary
    of harvest, non-harvest, and transport and weather to calculate them. dict(dict(boolean))
    '''
    def saveData(self, fertFeed, fertDist, pestFeed, operationDict, alloc):
        print 'Saving results to database...'
        # initialize database objects
        Fert = Fertilizer.Fertilizer(self.cont, fertFeed, fertDist) 
        Chem = Chemical.Chemical(self.cont, pestFeed)
        Comb = CombustionEmissions.CombustionEmissions(self.cont, operationDict, alloc)
        Update = UpdateDatabase.UpdateDatabase(self.cont)
        FugDust = FugitiveDust.FugitiveDust(self.cont)
        NEI = NEIComparison.NEIComparison(self.cont)
        
        # get feedstocks from the run_codes
        feedstockList = []
        for run_code in self.run_codes:
            if run_code[0:2] in feedstockList:
                pass
            else:
                feedstockList.append(run_code[0:2])
        
        
    #----------------------------------------------------------------
        #Create tables, Populate Fertilizer & Chemical tables.  
        for feedstock in feedstockList:
            Update.createTables(feedstock)
            Fert.setFertilizer(feedstock)
            Chem.setChemical(feedstock)
            print "Fertilizer and Chemical complete for " + feedstock
    #----------------------------------------------------------------
        
        
    #----------------------------------------------------------------    
        #Populate Combustion Emissions Tables
        print "Populating tables with combustion emissions..."
        Comb.populateTables(self.run_codes, self.modelRunTitle)
        Comb.updateSG()
        print "...COMPLETED populating tables with combustion emissions."
    #----------------------------------------------------------------
        
        
    #----------------------------------------------------------------
        #Fugitive Dust Emissions
        
        modelSG = False
        for run_code in self.run_codes:
            if not run_code.startswith('SG'):
                FugDust.setEmissions(run_code) 
                print "Fugitive Dust Emissions complete for " + run_code  
            else: 
                modelSG = True
              
        if modelSG:
            #It makes more sense to create fugitive dust emissions using a separate method
            operations = ['Transport', 'Harvest', 'Non-Harvest']
            for operation in operations:
                sgFugDust = FugitiveDust.SG_FugitiveDust(self.cont, operation)
                sgFugDust.setEmissions()
        
        
    #only run the following if all feedstocks are being modeled.
        if len(feedstockList) == 5:
    #----------------------------------------------------------------
            #allocate emissions for single pass methodology - see constructor for ability to allocate CG emissions
            print "Allocate single pass emissions between corn stover and wheat straw."
            SinglePassAllocation.SinglePassAllocation(self.cont)
    #----------------------------------------------------------------
            
            
    #----------------------------------------------------------------
            #Create NEI comparison
            
            #create a single table that has all emissions in this inventory
            print 'populating Summed Dimmesnions table'
            for feedstock in feedstockList:
                NEI.createSummedEmissionsTable(feedstock)
                
            #create tables that contain a ratio to NEI
            count = 0
            for feedstock in feedstockList:
                NEI.createNEIComparison(feedstock)
                if count == 4:
                    # on the last go, make a total query for all cellulosic.
                    NEI.createNEIComparison('cellulosic')
                count += 1
                    
            
    #----------------------------------------------------------------
    
    
    #----------------------------------------------------------------
            #create graphics and numerical summary 
            
            #Contribution Analysis
            print 'Creating emissions contribution figure.'
            ContributionFigure.ContributionAnalysis(self.cont)
            
            #Emissions Per Gallon
            print 'Creating emissions per gallon figure.'
            EmissionsPerGalFigure.EmissionsPerGallon(self.cont)
            
            # Emissions per a acre figure.
            print 'Creating emissions per acre figure.'
            EmissionsPerAcreFigure(self.cont)
            
            # Emissions per a production lb figure.
            print 'Creating emissions per lb figure.'
            EmissionPerProdFigure(self.cont)
            
            
            #Ratio to NEI
            RatioToNEIFigure.RatioToNEIFig(self.cont)
 
        
    #----------------------------------------------------------------
                    
        print 'Successful completion of model run.'


        
        
        