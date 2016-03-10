"""
Drives program.
Global Variables: model_run_title, run_codes, path, db, qr.
All stored in a Container.
Temporary Global Variables: run_code, fips, state, episode_year.
"""

import Container
import Batch
import QueryRecorder

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

from utils import config, logger
import MOVESModule

import os
import subprocess
import Logistics as Logistics
import Transportation
import pymysql


class Driver:

    def __init__(self, _model_run_title, run_codes, year_dict, _db):
        """
        Save important variables for the running of the program.

        @param _model_run_title: Scenario title.
        @param run_codes: Run codes to keep track of where you are in the program
        @param _db: Instantiation of Database class using scenario title
        @param year_dict: Dictionary of scenario years by feedstock type
        """

        # add run codes.
        self.run_codes = run_codes
        
        # add run title
        self.model_run_title = self._check_title(_model_run_title)

        # file paths and year for MOVES
        self.path_moves = config.get('moves_path')
        self.save_path_importfiles = os.path.join(config.get('moves_datafiles_path'), 'ImportFiles')
        self.save_path_runspecfiles = os.path.join(config.get('moves_datafiles_path'), 'RunSpecs')
        self.save_path_outputs = os.path.join(config.get('moves_datafiles_path'), 'Outputs')
        self.save_path_countyinputs = os.path.join(config.get('moves_datafiles_path'), 'County_Inputs')
        self.save_path_nationalinputs = os.path.join(config.get('moves_datafiles_path'), 'National_Inputs')
        self.yr = year_dict
        
        # get feedstocks from the run_codes
        self.feedstock_list = []
        for run_code in self.run_codes:
            if run_code[0:2] in self.feedstock_list:
                pass
            else:
                self.feedstock_list.append(run_code[0:2])
        
        # container to pass info around
        self.cont = Container.Container()
        self.cont.set(key='model_run_title', data=self.model_run_title)
        self.cont.set(key='run_codes', data=run_codes)
        self.cont.set(key='path', data='%s%s/' % (config.get('project_path'), _model_run_title, ))
        self.cont.set(key='db', data=_db)
        self.cont.set(key='qr', data=QueryRecorder.QueryRecorder(_path=self.cont.get('path')))

        # create Batch runner.
        self.batch = Batch.Batch(cont=self.cont)

    def _check_title(self, title):
        """
        Make sure the program is less then 8 characters and is not a run code.

        :param title: STRING to validate
        :return: <title>
        """

        # @TODO: refactor to return TRUE or FALSE

        try:
            assert len(title) <= 8
        except AssertionError:
            logger.error('Title (%s) must be 8 or less characters long' % (title, ))
            raise

        try:
            assert title not in self.run_codes
        except AssertionError:
            logger.error('Title (%s) must not be a run_code (%s)' % (title, ', '.join(self.run_codes)))
            raise

        return title

    def setup_nonroad(self):
        """
        Set up the NONROAD program by creating option, allocation, and population files.
        Also creates batch files to run.
        """

        # initialize objects
        scenario = Opt.ScenarioOptions(cont=self.cont)
        alo = Alo.Allocate(cont=self.cont)
        # create batch file.
        self.batch.get_master('w')

        # go to each run code.
        for run_code in self.run_codes:

            logger.info('Processing NONROAD setup for run code: %s' % (run_code, ))
            # query database for appropriate production data based on run_code:
            # fips, state, productions
            # TODO: should this return the data? And pass the data as a variable in Driver?
            scenario.get_data(run_code=run_code)
            scenario_year = self.yr[run_code[0:2]]            
            
            # initialize variables
            state = scenario.data[0][1]
            fips_prior = str(scenario.data[0][0])

            value = False
            if len(scenario.data[0]) >= 4:
                value = scenario.data[0][3] > 0.0
            if len(scenario.data[0]) >= 3:
                value = scenario.data[0][2] > 0.0

            if value is True:
                # New population object created for each run_code
                # Pop is the abstract class and .<type> is the concrete class.
                if run_code.startswith('CG_I'):
                    pop = Pop.CornGrainIrrigationPop(cont=self.cont, episode_year=scenario_year, run_code=run_code)
                elif run_code.endswith('L'):
                    pop = Pop.LoadingEquipment(cont=self.cont, episode_year=scenario_year, run_code=run_code)
                elif run_code.startswith('SG'):
                    pop = Pop.SwitchgrassPop(cont=self.cont, episode_year=scenario_year, run_code=run_code)
                elif run_code.startswith('FR'):
                    pop = Pop.ForestPop(cont=self.cont, episode_year=scenario_year, run_code=run_code)
                elif run_code.startswith('CS'):
                    pop = Pop.ResiduePop(cont=self.cont, episode_year=scenario_year, run_code=run_code)
                elif run_code.startswith('WS'):
                    pop = Pop.ResiduePop(cont=self.cont, episode_year=scenario_year, run_code=run_code)
                elif run_code.startswith('CG'):
                    pop = Pop.CornGrainPop(cont=self.cont, episode_year=scenario_year, run_code=run_code)

                # is it possible to instantiate new classes each time?
                alo.initialize_alo_file(state=state, run_code=run_code, episode_year=scenario_year)
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
                        Opt.NROptionFile(self.cont, state, fips_prior, run_code, scenario_year)
                        alo.write_sum_and_close(fips=fips_prior)
                        pop.finish_pop()
                        self.batch.append(state=state, run_code=run_code)

                        fips_prior = fips
                        state = dat[1]

                        # initialize new pop and allocation files.
                        alo.initialize_alo_file(state=state, run_code=run_code, episode_year=scenario_year)
                        pop.initialize_pop(dat=dat)
                        # indicator is harvested acres. Except for FR when it is produce.
                        indicator = dat[2]
                        alo.write_indicator(fips=fips, indicator=indicator)
                        pop.append_pop(fips=fips, dat=dat)

                # close allocation files
                Opt.NROptionFile(self.cont, state, fips_prior, run_code, scenario_year)
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

    def setup_moves(self, fips_list):
        """         
        Set up the MOVES program by creating input data files, XML files for data imports, and XML files for runspecs.
        Also creates batch files to 1) import data using MOVES County Data Manager and 2) run the MOVES program.
        
        @param fips_list: list of all county FIPS codes
        """
        
        # list of file paths for MOVES inputs and outputs   
        path_list = [self.save_path_importfiles, self.save_path_runspecfiles, self.save_path_outputs, self.save_path_countyinputs, self.save_path_nationalinputs]
        
        # check to make sure file paths exist, otherwise create them        
        for path in path_list:
            if not os.path.exists(path):
                os.makedirs(path)    

        i = 0
        outputs = dict()
        batch_run_dict = dict()
        for feed in self.feedstock_list:

            logger.info('Processing MOVES setup for feedstock: %s' % (feed, ))
            
            # initialize MOVESModule
            moves_mod = MOVESModule.MOVESModule(crop=feed, fips_list=fips_list, yr_list=self.yr, path_moves=self.path_moves,
                                                save_path_importfiles=self.save_path_importfiles, save_path_runspecfiles=self.save_path_runspecfiles,
                                                save_path_countyinputs=self.save_path_countyinputs, save_path_nationalinputs=self.save_path_nationalinputs)

            # @TODO: replace vmt_short_haul with database query to calculate county-level vehicle populations (need to get data first - could use sample data to get started)
            vmt_short_haul = 10000  # annual vehicle miles traveled by combination short-haul trucks
            pop_short_haul = 1  # population of combination short-haul trucks (assume one per trip and only run MOVES for single trip)

            if i == 0:
                # create national data files (only has to be run once for all crops so perform for first crop only after MOVESModule initiated)
                moves_mod.create_national_data()

            # create county-level data files
            moves_mod.create_county_data(vmt_short_haul=vmt_short_haul, pop_short_haul=pop_short_haul)

            # create XML import files          
            moves_mod.create_xml_import()

            # create XML run spec files
            moves_mod.create_xml_runspec()

            # create batch files for importing and running MOVES        
            outputs = moves_mod.create_batch_files()

            i += 1

            moves_mod.import_data(outputs['im_filename'])
            logger.debug('Batch file for importing data: %s' % (outputs['im_filename'], ))
            logger.debug('Batch file MOVES for importing data: %s' % (outputs['run_filename'], ))
            batch_run_dict[feed] = outputs['run_filename']

        return batch_run_dict

    def run_moves(self, batch_run_dict):
        """
        Run MOVES using the batch file generated in setup_MOVES
        @param batch_run_dict = dictionary of file names for MOVES batch runs (by feedstock type)
        """
        feed = 'CG'  # for feed in self.feedstock_list: @TODO: replace with loop to go through all feedstocks
        logger.info('Running MOVES for feedstock: %s' % (feed, ))
        logger.info('Batch file MOVES for importing data: %s' % (batch_run_dict[feed], ))

        # execute batch file and log output
        output = subprocess.Popen(batch_run_dict[feed], cwd=self.path_moves, stdout=subprocess.PIPE).stdout.read()
        logger.debug('Command line output: %s' % output)
    
    def save_data(self, fert_feed, fert_dist, pest_feed, operation_dict, alloc, fips_list):
        """
        Create and populate the schema with the emissions inventory.
        @param fert_feed: Dictionary containing each feedstock and whether to do fertilizer calculations.
        dict(boolean)
        @param fert_dist: The five numbers must add to 1 b/c they represent the percentage of
        each of the five fertilizers used. list(float)
        @param pest_feed: whether a feedstock should calculate the pesticides used. A dictionary of
        feedstocks to what to do. dict(boolean)
        @param operation_dict: Dictionary containing each feedstock. Each feedstock contains a dictionary
        of harvest, non-harvest, and transport and whether to calculate them. dict(dict(boolean))
        @param alloc:
        @param fips_list: list of FIPS codes
        """

        logger.info('Saving results to database')

        # initialize database objects
        fert = Fertilizer.Fertilizer(cont=self.cont, fert_feed_stock=fert_feed, fert_dist=fert_dist)
        chem = Chemical.Chemical(cont=self.cont, pest_feed=pest_feed)
        comb = CombustionEmissions.CombustionEmissions(cont=self.cont, operation_dict=operation_dict, alloc=alloc)
        update = UpdateDatabase.UpdateDatabase(cont=self.cont)
        fug_dust = FugitiveDust.FugitiveDust(cont=self.cont)
        nei = NEIComparison.NEIComparison(cont=self.cont)
        logistics = Logistics.Logistics(feedstock_list=self.feedstock_list, cont=self.cont)

        # compute emissions from off-farm transportation
        # first, join tables for average speed and "dayhour" and create new table for transportation data
        connection = pymysql.connect(host=config['MOVES_db_host'], user=config['MOVES_db_user'], password=config['MOVES_db_pass'], db=config['MOVES_database'])
        cursor = connection.cursor()

        kvals = dict()
        kvals['fips'] = fips_list[0]  # avg speed distribution is the same for all FIPS codes
        kvals['feedstock'] = self.feedstock_list[0]  # and for all crops, so just pick one from each list
        kvals['scenario_name'] = self.model_run_title
        kvals['MOVES_database'] = config['MOVES_database']

        # generate average speed table
        # @ TODO: assumes schema "output_{scenarion_name}" already exists, need to fix this elsewhere
        # @ TODO: may want to move this query for table creation to another location
        query = """DROP TABLE IF EXISTS output_{scenario_name}.averagespeed;
                   CREATE TABLE output_{scenario_name}.averagespeed
                   AS (SELECT table1.roadTypeID, table1.avgSpeedBinID, table1.avgSpeedFraction, table2.hourID, table2.dayID, table1.hourDayID
                   FROM fips_{fips}_{feedstock}_in.avgspeeddistribution table1
                   LEFT JOIN {MOVES_database}.hourday table2
                   ON table1.hourDayID = table2.hourDayID);""".format(**kvals)

        # create transportation output table
        #  @ TODO: may want to move this query for table creation to another location
        query += """DROP TABLE IF EXISTS output_{scenario_name}.transportation;
                   CREATE TABLE output_{scenario_name}.transportation (fips char(5),
                                                                       feedstock varchar(5),
                                                                       yearID char(4),
                                                                       pollutantID varchar(45),
                                                                       run_emissions float,
                                                                       start_hotel_emissions float,
                                                                       rest_evap_emissions float DEFAULT 0,
                                                                       total_emissions_per_trip float,
                                                                       number_trips float,
                                                                       total_emissions float);""".format(**kvals)
        # create transportation output table
        #  @ TODO: may want to move this query for table creation to another location
        query += """DROP TABLE IF EXISTS output_{scenario_name}.fugitive_dust;
                   CREATE TABLE output_{scenario_name}.fugitive_dust (fips char(5),
                                                                     feedstock varchar(5),
                                                                     yearID char(4),
                                                                     pollutantID varchar(45),
                                                                     logistics_type varchar (2),
                                                                     unpaved_fd_emissions float,
                                                                     sec_paved_fd_emissions float,
                                                                     total_fd_emissions float);""".format(**kvals)

        cursor.execute(query)
        cursor.close()

        # now loop through feedstocks and FIPS codes to compute respective emissions
        self.feedstock_list = ['CG']
        for feedstock in self.feedstock_list:
            for fips in fips_list:
                vmt = 10000  # @TODO: replace with query to get correct county-level VMT data
                pop = 1  # @TODO: assuming only one vehicle per trip
                s = 3.9  # @TODO: replace with query to get correct silt data for county
                transportation = Transportation.Transportation(feed=feedstock, cont=self.cont, fips=fips, vmt=vmt, pop=pop, s=s)
                transportation.calculate_transport_emissions()

        # Create tables, Populate Fertilizer & Chemical tables.
        for feedstock in self.feedstock_list:
            update.create_tables(feedstock=feedstock)
            fert.set_fertilizer(feed=feedstock)
            chem.set_chemical(feed=feedstock)
            logger.info("Fertilizer and Chemical complete for " + feedstock)  # @TODO: convert to string formatting

        # Populate Combustion Emissions Tables
        logger.info("Populating tables with combustion emissions")
        comb.populate_tables(run_codes=self.run_codes)
        for run_code in self.run_codes:
            if run_code.startswith('SG'):
                if not run_code.endswith('L'):
                    comb.update_sg()
        logger.info("COMPLETED populating tables with combustion emissions")

        # Fugitive Dust Emissions
        modelsg = False
        for run_code in self.run_codes:
            if not run_code.startswith('SG'):
                if not run_code.endswith('L'):
                    fug_dust.set_emissions(run_code=run_code)
                    logger.info("Fugitive Dust Emissions complete for " + run_code)  # @TODO: convert to string formatting
            else:
                if not run_code.endswith('L'):
                    modelsg = True

        if modelsg:
            # It makes more sense to create fugitive dust emissions using a separate method
            operations = ['Transport', 'Harvest', 'Non-Harvest']
            for operation in operations:
                sgfug_dust = FugitiveDust.SG_FugitiveDust(cont=self.cont, operation=operation)
                sgfug_dust.set_emissions()

        # only run the following if all feedstocks are being modeled.
        if len(self.feedstock_list) == 5:
            # allocate emissions for single pass methodology - see constructor for ability to allocate CG emissions
            logger.info("Allocate single pass emissions between corn stover and wheat straw.")
            SinglePassAllocation.SinglePassAllocation(cont=self.cont)

            # Create nei comparison

            # create a single table that has all emissions in this inventory
            logger.info('populating Summed Dimmensions table')
            for feedstock in self.feedstock_list:
                nei.create_summed_emissions_table(feedstock=feedstock)

            # create tables that contain a ratio to NEI
            count = 0
            for feedstock in self.feedstock_list:
                nei.create_nei_comparison(feedstock=feedstock)
                if count == 4:
                    # on the last go, make a total query for all cellulosic.
                    nei.create_nei_comparison(feedstock='cellulosic')
                count += 1

        # compute emissions and electricity associated with logistics
        logistics.calc_logistics()

        # create graphics and numerical summary

        if config.get('figure_plotting') is True:
            # Contribution Analysis
            logger.info('Creating emissions contribution figure.')
            ContributionFigure.ContributionAnalysis(cont=self.cont)

            # Emissions Per Gallon
            logger.info('Creating emissions per gallon figure.')
            EmissionsPerGalFigure.EmissionsPerGallon(self.cont)

            # Emissions per a acre figure.
            logger.info('Creating emissions per acre figure.')
            EmissionsPerAcreFigure(self.cont)

            # Emissions per a production lb figure.
            logger.info('Creating emissions per lb figure.')
            EmissionPerProdFigure(self.cont)

            # Ratio to NEI
            RatioToNEIFigure.RatioToNEIFig(self.cont)

        logger.info('Successful completion of model run.')

if __name__ == '__main__':
    raise NotImplementedError
