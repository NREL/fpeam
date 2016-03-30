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


class Driver:

    def __init__(self, model_run_title, run_codes, year_dict, db):
        """
        Save important variables for the running of the program.

        :param model_run_title: Scenario title.
        :param run_codes: Run codes to keep track of where you are in the program
        :param db: Instantiation of Database class using scenario title
        :param year_dict: Dictionary of scenario years by feedstock type
        """

        # add run codes
        self.run_codes = run_codes
        
        # add run title
        self._check_title(model_run_title)
        self.model_run_title = model_run_title

        # get constants_schema
        self.constants_schema = config.get('constants_schema')

        # file paths and year for MOVES
        self.path_moves = config.get('moves_path')
        self.save_path_importfiles = os.path.join(config.get('moves_datafiles_path'), 'import_files')
        self.save_path_runspecfiles = os.path.join(config.get('moves_datafiles_path'), 'run_specs')
        self.save_path_outputs = os.path.join(config.get('moves_datafiles_path'), 'outputs')
        self.save_path_countyinputs = os.path.join(config.get('moves_datafiles_path'), 'county_inputs')
        self.save_path_nationalinputs = os.path.join(config.get('moves_datafiles_path'), 'national_inputs')
        self.yr = year_dict

        # get feedstocks from the run_codes
        self.feedstock_list = set()
        for run_code in self.run_codes:
            self.feedstock_list.add(run_code[0:2])

        # get feedstock list for transportation data
        self.transport_feed_list = config.get('transport_feed_list')

        # get yield list for transport data
        self.yield_list = config.get('yield_list')

        # get toggle for running moves by crop
        moves_by_crop = config.get('moves_by_crop')
        # set moves feedstock list depending on toggle for moves_by_crop
        if moves_by_crop is True:
            self.moves_feedstock_list = self.feedstock_list
        else:
            self.moves_feedstock_list = ['all_crops']

        # get list of logistics system(s) being modeled
        self.logistics_list = config.get('logistics_type')

        # create kvals dictionary for string formatting
        self.kvals = {'constants_schema': config.get('constants_schema'),
                      'production_schema': config.get('production_schema'),
                      'moves_database': config.get('moves_database'),
                      'moves_output_db': config.get('moves_output_db'),
                      'nei_data_by_county': config.get('nei_data_by_county'),
                      'feed_tables': config.get('feed_tables'),
                      'chem_tables': config.get('chem_tables'),
                      'scenario_name': model_run_title}

        for feed in self.feedstock_list:
            feed = feed.lower()
            self.kvals['%s_chem_table' % (feed,)] = self.kvals['chem_tables'][feed]
            self.kvals['%s_table' % (feed, )] = self.kvals['feed_tables'][feed]

        # container to pass info around
        self.cont = Container.Container()
        self.cont.set(key='model_run_title', data=self.model_run_title)
        self.cont.set(key='run_codes', data=run_codes)
        self.cont.set(key='path', data=os.path.join(config.get('project_path'), model_run_title))
        self.cont.set(key='db', data=db)
        self.cont.set(key='qr', data=QueryRecorder.QueryRecorder(_path=self.cont.get('path')))
        self.cont.set(key='kvals', data=self.kvals)

        # create Batch runner
        self.batch = Batch.Batch(cont=self.cont)

        # set database object
        self.db = db

    def _check_title(self, title):
        """
        Make sure the program is less then 8 characters and is not a run code.

        :param title: STRING to validate
        :return: True (or raise Exception for violations)
        """

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

        return True

    def setup_nonroad(self):
        """
        Set up the NONROAD program by creating option, allocation, population, and batch files.

        :return:
        """

        # initialize objects
        scenario = Opt.ScenarioOptions(cont=self.cont)
        alo = Alo.Allocate(cont=self.cont)

        # initialize batch file
        self.batch.get_master('w')

        # go to each run code.
        for run_code in self.run_codes:

            logger.info('Processing NONROAD setup for run code: %s' % (run_code, ))

            # query database for appropriate production data based on run_code:
            # fips, state, productions
            scenario.get_data(run_code=run_code)
            scenario_year = self.yr[run_code[0:2]]            
            
            # initialize variables
            state = scenario.data[0][1]  # get the first state
            fips_prior = str(scenario.data[0][0])  # get the first FIPS

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

            alo.initialize_alo_file(state=state, run_code=run_code, episode_year=scenario_year)
            pop.initialize_pop(dat=scenario.data[0])

            self.batch.initialize(run_code)

            # go through each row of the data table
            for dat in scenario.data:
                # check to see if production is greater than zero
                prod_greater_than_zero = False
                if len(dat) >= 4:
                    prod_greater_than_zero = dat[3] > 0.0
                if len(dat) >= 3:
                    prod_greater_than_zero = dat[2] > 0.0

                # if production is greater than zero, then append equipment information to population file
                if prod_greater_than_zero is True:
                    fips = str(dat[0])
                    # The db table is ordered alphabetically.
                    # The search will look through a state. When the state changes in the table,
                    # then the loop will go to the else, closing the old files. and initializing new files.

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

        # save path for running batch files
        # @TODO: does this need to be here?
        self.path = scenario.path

    def run_nonroad(self, qprocess):
        """
        Run the NONROAD program by opening the batch files.
        :param qprocess: sub process controller from the Controller.

        Used to control the flow of the NONROAD program within the application.
        """

        self.batch.run(qprocess)

    def setup_moves(self, fips):
        """         
        Set up the MOVES program by creating input data files, XML files for data imports, and XML files for runspecs.
        Also creates batch files to 1) import data using MOVES County Data Manager and 2) run the MOVES program.
        
        :param fips: county FIPS code
        """
        db = self.cont.get('db')

        # create table for moves metadata
        query = "CREATE TABLE IF NOT EXISTS {constants_schema}.moves_metadata (scen_id text);".format(**self.kvals)
        db.create(query)

        # list of file paths for MOVES inputs and outputs   
        path_list = [self.save_path_importfiles, self.save_path_runspecfiles, self.save_path_outputs, self.save_path_countyinputs, self.save_path_nationalinputs]
        
        # check to make sure file paths exist, otherwise create them        
        for path in path_list:
            if not os.path.exists(path):
                os.makedirs(path)    

        batch_run_dict = dict()
        for i, feed in enumerate(self.moves_feedstock_list):
            logger.info('Processing MOVES setup for feedstock: %s, fips: %s' % (feed, fips, ))
            
            # initialize MOVESModule
            moves_mod = MOVESModule.MOVESModule(crop=feed, fips=fips, yr_list=self.yr, path_moves=self.path_moves,
                                                save_path_importfiles=self.save_path_importfiles, save_path_runspecfiles=self.save_path_runspecfiles,
                                                save_path_countyinputs=self.save_path_countyinputs, save_path_nationalinputs=self.save_path_nationalinputs, db=db)

            # default values used for running MOVES, actual VMT later used in save_data to compute total emission
            # @TODO: if we decide that rates does vary with VMT, replace vmt_short_haul with database query to calculate county-level VMT (need to get data into database first)
            vmt_short_haul = config.as_int('vmt_short_haul')  # annual vehicle miles traveled by combination short-haul trucks
            pop_short_haul = config.as_int('pop_short_haul')  # population of combination short-haul trucks (assume one per trip and only run MOVES for single trip)

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

            # only import data if MOVES output does not already exist for this FIPS, yearID, monthID, and dayID
            if outputs['moves_output_exists'] is False:
                moves_mod.import_data(outputs['im_filename'])

            logger.debug('Batch file for importing data: %s' % (outputs['im_filename'], ))
            logger.debug('Batch file MOVES for importing data: %s' % (outputs['run_filename'], ))
            batch_run_dict[feed] = outputs['run_filename']

        return batch_run_dict

    def run_moves(self, batch_run_dict, fips):
        """
        Run MOVES using the batch file generated in setup_MOVES

        :param batch_run_dict = dictionary of file names for MOVES batch runs (by feedstock type)
        :param fips = fips code for county
        :return:
        """

        for feed in self.moves_feedstock_list:

            # check if batch run dictionary contains any files
            if batch_run_dict[feed] is not None:
                # if so, execute batch file and log output
                logger.info('Running MOVES for feedstock: %s, fips: %s' % (feed, fips))
                logger.info('Batch file MOVES for importing data: %s' % (batch_run_dict[feed], ))

                output = subprocess.Popen(batch_run_dict[feed], cwd=self.path_moves, stdout=subprocess.PIPE).stdout.read()
                logger.debug('Command line output: %s' % output)

                self.kvals['moves_scen_id'] = "{fips}_{crop}_{year}_{month}_{day}".format(fips=fips, crop=feed, day=config.get('moves_timespan')['d'][0], month=config.get('moves_timespan')['mo'][0], year=self.yr[feed])
                query_moves_metadata = """  INSERT INTO {constants_schema}.moves_metadata(scen_id)
                                            VALUES ('{moves_scen_id}')""".format(**self.kvals)
                self.db.input(query_moves_metadata)
            else:
                # otherwise, report that MOVES run already complete
                logger.info('MOVES run already complete for feedstock: %s, fips: %s' % (feed, fips))
    
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

        kvals = dict()
        kvals['fips'] = fips_list[0]  # avg speed distribution is the same for all FIPS codes
        kvals['feedstock'] = list(self.moves_feedstock_list)[0]  # and for all crops, so just pick one from each list
        kvals['scenario_name'] = self.model_run_title
        kvals['MOVES_database'] = config['moves_database']
        kvals['moves_output_db'] = config.get('moves_output_db')

        # generate average speed table
        # @ TODO: creates schema "output_{scenario_name}" - might want to do this elsewhere
        # @ TODO: may want to move this query for table creation to another location
        query = """CREATE SCHEMA IF NOT EXISTS output_{scenario_name};
                   DROP TABLE IF EXISTS output_{scenario_name}.averageSpeed;
                   CREATE TABLE output_{scenario_name}.averageSpeed
                   AS (SELECT table1.roadTypeID, table1.avgSpeedBinID, table1.avgSpeedFraction, table2.hourID, table2.dayID, table1.hourDayID
                   FROM fips_{fips}_{feedstock}_in.avgspeeddistribution table1
                   LEFT JOIN {MOVES_database}.hourday table2
                   ON table1.hourDayID = table2.hourDayID);""".format(**kvals)
        self.db.create(query)

        # create transportation output table
        #  @ TODO: may want to move this query for table creation to another location
        query = """DROP TABLE IF EXISTS output_{scenario_name}.transportation;
                   CREATE TABLE output_{scenario_name}.transportation (fips char(5),
                                                                       feedstock varchar(5),
                                                                       yearID char(4),
                                                                       logistics_type char(2),
                                                                       pollutantID varchar(45),
                                                                       run_emissions float,
                                                                       start_hotel_emissions float,
                                                                       rest_evap_emissions float DEFAULT 0,
                                                                       total_emissions_per_trip float,
                                                                       number_trips float,
                                                                       total_emissions float);""".format(**kvals)
        self.db.create(query)

        # create transportation output table
        #  @ TODO: may want to move this query for table creation to another location
        query = """DROP TABLE IF EXISTS output_{scenario_name}.fugitive_dust;
                   CREATE TABLE output_{scenario_name}.fugitive_dust (fips char(5),
                                                                     feedstock varchar(5),
                                                                     yearID char(4),
                                                                     pollutantID varchar(45),
                                                                     logistics_type varchar (2),
                                                                     unpaved_fd_emissions float,
                                                                     sec_paved_fd_emissions float,
                                                                     total_fd_emissions float);""".format(**kvals)

        self.db.create(query)

        # now loop through feedstocks and FIPS codes to compute respective transportation emissions
        for feedstock in self.feedstock_list:
            if feedstock in self.transport_feed_list:
                for yield_type in self.yield_list:
                    for fips in fips_list:
                        for logistics_type in self.logistics_list:
                            vmt = 100  # @TODO: replace with query to get correct county-level VMT data
                            pop = 1  # @TODO: assuming only one vehicle per trip
                            silt = 3.9  # @TODO: replace with query to get correct silt data for county
                            transportation = Transportation.Transportation(feed=feedstock, cont=self.cont, fips=fips, vmt=vmt, pop=pop, logistics_type=logistics_type, silt=silt, yield_type=yield_type)
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
                    comb.update_sg(run_code=run_code)
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

        if modelsg is True:
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
        logistics.calc_logistics(run_codes=self.run_codes, feedstock_list=self.feedstock_list, logistics_list=self.logistics_list)

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
