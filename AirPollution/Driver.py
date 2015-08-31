"""
Drives program.
Global Variables: model_run_title, run_codes, path, db, qr.
All stored in a Container.
Temporary Global Variables: run_code, fips, state, episode_year.
"""


import Container
import Batch
from model.Database import Database
import QueryRecorder
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


class Driver:
    
    def __init__(self, _model_run_title, run_codes, _db):
        """
        Save important variables for the running of the program.
        @param _model_run_title: Scenario title.
        @param run_codes: Run codes to keep track of where you are in the program
        @param _db:
        """

        # add run codes.
        self.run_codes = run_codes
        # add run title.
        self.model_run_title = self._check_title(_model_run_title)
        # container to pass info around.
        self.cont = Container.Container()
        self.cont.set(key='model_run_title', data=self.model_run_title)
        self.cont.set(key='run_codes', data=run_codes)
        self.cont.set(key='path', data='C:/Nonroad/%s/' % (_model_run_title, ))  # @TODO: remove hardcoded path
        self.cont.set(key='db', data=_db)
        self.cont.set(key='qr', data=QueryRecorder.QueryRecorder(_path=self.cont.get('path')))
        # create Batch runner.
        self.batch = Batch.Batch(cont=self.cont)

    def _check_title(self, title):
        """
        Make sure the program is less then 8 characters.
        @param title: Title of the program.
        """
        try:
            assert len(title) <= 8
        except AssertionError:
            print "Title must be 8 or less characters long"  # @TODO: convert to logger
            raise

        try:
            assert title not in self.run_codes
        except AssertionError:
            print 'Title must not be a run_code (%s)' % (', '.join(self.run_codes))  # @TODO: convert to logger
            raise

        return title

    def setup_nonroad(self):
        """
        Set up the NONROAD program by creating option, allocation, and population files.
        Also creates batch files to run.
        """
        # @TODO: maybe should make episode_year to be a global variable in this class instead of Options.

        # initialize objects
        scenario = Opt.ScenarioOptions(cont=self.cont)
        alo = Alo.Allocate(cont=self.cont)
        # create batch file.
        self.batch.get_master('w')

        # go to each run code.
        for run_code in self.run_codes:

            print run_code  # @TODO: convert to logger
            # query database for appropriate production data based on run_code:
            # fips, state, productions
            # TODO: should this return the data? And pass the data as a variable in Driver?
            scenario.get_data(run_code=run_code)

            # initialize variables
            state = scenario.data[0][1]
            fips_prior = str(scenario.data[0][0])

            # New population object created for each run_code
            # Pop is the abstract class and .<type> is the concrete class.
            if run_code.startswith('CG_I'):
                pop = Pop.CornGrainIrrigationPop(cont=self.cont, episode_year=scenario.episode_year, run_code=run_code)
            elif run_code.startswith('SG'):
                pop = Pop.SwitchgrassPop(cont=self.cont, episode_year=scenario.episode_year, run_code=run_code)
            elif run_code.startswith('FR'):
                pop = Pop.ForestPop(cont=self.cont, episode_year=scenario.episode_year, run_code=run_code)
            elif run_code.startswith('CS'):
                pop = Pop.ResiduePop(cont=self.cont, episode_year=scenario.episode_year, run_code=run_code)
            elif run_code.startswith('WS'):
                pop = Pop.ResiduePop(cont=self.cont, episode_year=scenario.episode_year, run_code=run_code)
            elif run_code.startswith('CG'):
                pop = Pop.CornGrainPop(cont=self.cont, episode_year=scenario.episode_year, run_code=run_code)

            # is it possible to instantiate new classes each time?
            alo.initialize_alo_file(state=state, run_code=run_code, episode_year=scenario.episode_year)
            pop.initialize_pop(dat=scenario.data[0])
            self.batch.initialize(run_code)

            # go through each row of the data table.
            for dat in scenario.data:
                fips = str(dat[0])
                # The db table is ordered alphabetically.
                # The search will look through a state. When the state changes in the table,
                # then the loop will go to the else, closing the old files. and initializing new files.

                # @TODO: verify ORDER BY clause orders by state
                # dat[1] is the state.
                if dat[1] == state:
                    # indicator is harvested acres. Except for FR when it is produce.
                    indicator = dat[2]
                    alo.write_indicator(fips=fips, indicator=indicator)
                    pop.append_pop(fips=fips, dat=dat)
                # last time through a state, will close different files, and start new ones.
                else:
                    # write *.opt file, close allocation file, close *.pop file
                    Opt.NROptionFile(self.cont, state, fips_prior, run_code, scenario.episode_year)
                    alo.write_sum_and_close(fips=fips_prior)
                    pop.finish_pop()
                    self.batch.append(state=state, run_code=run_code)

                    fips_prior = fips
                    state = dat[1]

                    # initialize new pop and allocation files.
                    alo.initialize_alo_file(state=state, run_code=run_code, episode_year=scenario.episode_year)
                    pop.initialize_pop(dat=dat)
                    # indicator is harvested acres. Except for FR when it is produce.
                    indicator = dat[2]
                    alo.write_indicator(fips=fips, indicator=indicator)
                    pop.append_pop(fips=fips, dat=dat)

                    # close allocation files
            Opt.NROptionFile(self.cont, state, fips_prior, run_code, scenario.episode_year)
            alo.write_sum_and_close(fips=fips_prior)
            pop.finish_pop()
            self.batch.append(state=state, run_code=run_code)
            self.batch.finish(run_code=run_code)

        # close scenariobatchfile
        self.batch.scenario_batch_file.close()
        # save path for running batch files.
        # @TODO: does this need to be here?
        self.path = scenario.path

    def run_nonroad(self, qprocess):
        """
        Run the NONROAD program by opening the batch files.
        @param qprocess: sub process controller from the Controller.
        Used to control the flow of the NONROAD program within the application.
        """
        self.batch.run(qprocess)
        
    def save_data(self, fert_feed, fert_dist, pest_feed, operation_dict, alloc):
        """
        Create and populate the schema with the emissions inventory.
        @param fert_feed: Dictionary containing each feedstock and weather to do fertilizer calculations.
        dict(boolean)
        @param fert_dist: The five numbers must add to 1 b/c they represent the percentage of
        each of the five fertilizers used. list(float)
        @param pest_feed: Weather a feedstock should calculate the pesticides used. A dictionary of
        feedstocks to what to do. dict(boolean)
        @param operation_dict: Dictionary containing each feedstock. Each feedstock contains a dictionary
        of harvest, non-harvest, and transport and weather to calculate them. dict(dict(boolean))
        """

        print 'Saving results to database...'  # @TODO: convert to logger

        # initialize database objects
        fert = Fertilizer.Fertilizer(cont=self.cont, fert_feed_stock=fert_feed, fert_dist=fert_dist)
        chem = Chemical.Chemical(cont=self.cont, pest_feed=pest_feed)
        comb = CombustionEmissions.CombustionEmissions(cont=self.cont, operation_dict=operation_dict, alloc=alloc)
        update = UpdateDatabase.UpdateDatabase(cont=self.cont)
        fug_dust = FugitiveDust.FugitiveDust(cont=self.cont)
        nei = NEIComparison.NEIComparison(cont=self.cont)
        
        # get feedstocks from the run_codes
        feedstock_list = []
        for run_code in self.run_codes:
            if run_code[0:2] in feedstock_list:
                pass
            else:
                feedstock_list.append(run_code[0:2])

        # Create tables, Populate Fertilizer & Chemical tables.
        for feedstock in feedstock_list:
            update.create_tables(feedstock=feedstock)
            fert.set_fertilizer(feed=feedstock)
            chem.set_chemical(feed=feedstock)
            print "Fertilizer and Chemical complete for " + feedstock  # @TODO: convert to logger

        # Populate Combustion Emissions Tables
        print "Populating tables with combustion emissions..."  # @TODO: convert to logger
        comb.populate_tables(run_codes=self.run_codes)
        comb.update_sg()
        print "...COMPLETED populating tables with combustion emissions."  # @TODO: convert to logger

        # Fugitive Dust Emissions
        modelSG = False
        for run_code in self.run_codes:
            if not run_code.startswith('SG'):
                fug_dust.set_emissions(run_code=run_code)
                print "Fugitive Dust Emissions complete for " + run_code  # @TODO: convert to logger
            else: 
                modelSG = True

        if modelSG:
            # It makes more sense to create fugitive dust emissions using a separate method
            operations = ['Transport', 'Harvest', 'Non-Harvest']
            for operation in operations:
                sgfug_dust = FugitiveDust.SG_FugitiveDust(cont=self.cont, operation=operation)
                sgfug_dust.set_emissions()

        # only run the following if all feedstocks are being modeled.
        if len(feedstock_list) == 5:
            # allocate emissions for single pass methodology - see constructor for ability to allocate CG emissions
            print "Allocate single pass emissions between corn stover and wheat straw."  # @TODO: convert to logger
            SinglePassAllocation.SinglePassAllocation(cont=self.cont)

            # Create nei comparison

            # create a single table that has all emissions in this inventory
            print 'populating Summed Dimmesnions table'  # @TODO: convert to logger
            for feedstock in feedstock_list:
                nei.create_summed_emissions_table(feedstock=feedstock)

            # create tables that contain a ratio to NEI
            count = 0
            for feedstock in feedstock_list:
                nei.create_nei_comparison(feedstock=feedstock)
                if count == 4:
                    # on the last go, make a total query for all cellulosic.
                    nei.create_nei_comparison(feedstock='cellulosic')
                count += 1

        # create graphics and numerical summary
            
        # Contribution Analysis
        print 'Creating emissions contribution figure.'  # @TODO: convert to logger
        ContributionFigure.ContributionAnalysis(cont=self.cont)
            
        # Emissions Per Gallon
        print 'Creating emissions per gallon figure.'  # @TODO: convert to logger
        EmissionsPerGalFigure.EmissionsPerGallon(self.cont)
            
        # Emissions per a acre figure.
        print 'Creating emissions per acre figure.'  # @TODO: convert to logger
        EmissionsPerAcreFigure(self.cont)
            
        # Emissions per a production lb figure.
        print 'Creating emissions per lb figure.'  # @TODO: convert to logger
        EmissionPerProdFigure(self.cont)

        # Ratio to NEI
        RatioToNEIFigure.RatioToNEIFig(self.cont)

        print 'Successful completion of model run.'  # @TODO: convert to logger
