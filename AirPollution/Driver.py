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

    def __init__(self, model_run_title, run_codes, year_dict, db, moves_fips_list):
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

        # folder path for MOVES data files
        moves_datafiles_path = config.get('moves_datafiles_path')

        # file paths and year for MOVES
        self.path_moves = config.get('moves_path')
        self.save_path_importfiles = os.path.join(moves_datafiles_path, 'import_files')
        self.save_path_runspecfiles = os.path.join(moves_datafiles_path, 'run_specs')
        self.save_path_outputs = os.path.join(moves_datafiles_path, 'outputs')
        self.save_path_countyinputs = os.path.join(moves_datafiles_path, 'county_inputs')
        self.save_path_nationalinputs = os.path.join(moves_datafiles_path, 'national_inputs')

        self.yr = year_dict

        # get feedstocks from the run_codes
        self.feedstock_list = set()
        for run_code in self.run_codes:
            self.feedstock_list.add(run_code[0:2])

        # get feedstock list for transportation data
        self.transport_feed_list = config.get('transport_feed_list')

        # get transport data feedstock columns
        self.feed_id_dict = config.get('feed_id_dict')

        # get list of columns for transportation data
        self.transport_col = config.get('transport_column')

        # get feedstock type dictionary
        self.feed_type_dict = config.get('feed_type_dict')

        # get transportation table dictionary
        self.transport_table_dict = config.get('transport_table_dict')

        # get yield list for transport data
        self.scenario_yield = config.get('yield')
        
        # get scenario year
        self.scenario_year = config.get('year_dict')['all_crops']

        # get toggle for running moves by state-level fips
        self.moves_state_level = config.get('state_level_moves')

        # get toggle for running moves by crop
        moves_by_crop = config.get('moves_by_crop')        
        
        # set moves feedstock list depending on toggle for moves_by_crop
        if moves_by_crop is True:
            self.moves_feedstock_list = self.feedstock_list
        else:
            self.moves_feedstock_list = ['all_crops', ]

        # get list of logistics system(s) being modeled
        self.logistics_list = config.get('logistics_type')

        # create kvals dictionary for string formatting
        self.kvals = {'constants_schema': config.get('constants_schema'),
                      'production_schema': config.get('production_schema'),
                      'moves_database': config.get('moves_database'),
                      'moves_output_db': config.get('moves_output_db'),
                      'nei_data_by_county': config.get('nei_data_by_county'),
                      'feed_tables': config.get('feed_tables'),  # @TODO: these names can probably be hardcoded
                      'chem_tables': config.get('chem_tables'),
                      'scenario_name': model_run_title}

        for feed in self.feedstock_list:
            feed = feed.lower()
            self.kvals['%s_chem_table' % (feed, )] = self.kvals['chem_tables'][feed]
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

        # years for crop budgets (energy crops have multiple years; conventional crops only single year)
        self.years_budget = config.get('crop_budget_dict')['years']

        # set fips list for post-processing moves data
        self.moves_fips_list = moves_fips_list

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

    def setup_nonroad(self, regional_crop_budget):
        """
        Set up the NONROAD program by creating option, allocation, population, and batch files.

        :param regional_crop_budget: toggle for whether to use regional or national crop budget
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

            # get data from the database (scenario.data = [fips, state fips, production, harvested acreage, equipment type, horsepower, hours per year (for population)])
            scenario.get_data(run_code=run_code, regional_crop_budget=regional_crop_budget)

            # create output directories that correspond to state and run code
            scenario.create_output_dir(run_code=run_code)

            # get the year for the scenario
            scenario_year = self.yr[run_code[0:2]]            
            
            # get the first state and fips code in the list of data for the run code
            if scenario.data is not None:
                state = scenario.data[0][0][1]
                fips_prior = str(scenario.data[0][0][0])

                # check if regional crop budget should be used
                if regional_crop_budget is False:  # if not, run with national budget
                    # new population object created for each run_code, where Pop is the abstract class and .<type> is the concrete class
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
                else:  # if regional crop budget should be used
                    # get irrigation data for corn grain using the same method as for national budget
                    if run_code.startswith('CG_I'):
                        pop = Pop.CornGrainIrrigationPop(cont=self.cont, episode_year=scenario_year, run_code=run_code)
                    # get loading equipment if run code ends with L (except for forestry because loading equipment is included in the crop budget)
                    elif run_code.endswith('L') and not run_code.startswith('F'):
                        pop = Pop.LoadingEquipment(cont=self.cont, episode_year=scenario_year, run_code=run_code)
                    # for all other run codes, use regional crop budgets
                    else:
                        pop = Pop.RegionalEquipment(cont=self.cont, episode_year=scenario_year, run_code=run_code)

                # initialize allocation, population, and batch files
                alo.initialize_alo_file(state=state, run_code=run_code, episode_year=scenario_year)
                pop.initialize_pop(dat=scenario.data[0][0])
                self.batch.initialize(run_code)

                # go through each row of the data table for this run code
                for dat in scenario.data[0]:
                    # check to see if production is greater than zero
                    prod_greater_than_zero = dat[3] > 0.0  # dat[2] is the production

                    # if production is greater than zero, then append equipment information to population file
                    if prod_greater_than_zero is True:
                        fips = str(dat[0])
                        # bdgt = str(dat[5])
                        # The db table is ordered alphabetically.
                        # The search will look through a state. When the state changes in the table,
                        # then the loop will go to the else, closing the old files. and initializing new files.

                        # dat[1] is the state.
                        if dat[1] == state:
                            # indicator is harvested acres. Except for FR when it is produce.
                            if run_code.startswith('F'):
                                indicator = dat[3]
                            else:
                                indicator = dat[2]
                            alo.write_indicator(fips=fips, indicator=indicator)

                            # append data to population file
                            pop.append_pop(fips=fips, dat=dat)
                        # last time through a state, will close different files, and start new ones.
                        else:
                            # write *.opt file, close allocation file, close *.pop file
                            Opt.NROptionFile(self.cont, state, fips_prior, run_code, scenario_year)
                            alo.write_sum_and_close(fips=fips_prior)
                            pop.finish_pop()

                            # add state and run code to batch file for running NONROAD
                            self.batch.append(state=state, run_code=run_code)

                            # update fips_prior and state to this fips and state
                            fips_prior = fips
                            state = dat[1]

                            # initialize new pop and allocation files.
                            alo.initialize_alo_file(state=state, run_code=run_code, episode_year=scenario_year)
                            pop.initialize_pop(dat=dat)

                            # indicator is harvested acres. Except for FR when it is produce.
                            if run_code.startswith('F'):
                                indicator = dat[3]
                            else:
                                indicator = dat[2]
                            alo.write_indicator(fips=fips, indicator=indicator)

                            # append data to population file
                            pop.append_pop(fips=fips, dat=dat)

                # close allocation files
                Opt.NROptionFile(self.cont, state, fips_prior, run_code, scenario_year)
                alo.write_sum_and_close(fips=fips_prior)
                pop.finish_pop()

                # append final file for batch run with this run code
                self.batch.append(state=state, run_code=run_code)

                # finish batch file for this run code
                self.batch.finish(run_code=run_code)

        # close scenariobatchfile
        self.batch.scenario_batch_file.close()

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
            logger.info('Processing MOVES setup for feedstock: %s, fips: %s' % (feed, fips))
            
            # initialize MOVESModule
            moves_mod = MOVESModule.MOVESModule(crop=feed, fips=fips, yr_list=self.yr, path_moves=self.path_moves,
                                                save_path_importfiles=self.save_path_importfiles, save_path_runspecfiles=self.save_path_runspecfiles,
                                                save_path_countyinputs=self.save_path_countyinputs, save_path_nationalinputs=self.save_path_nationalinputs, db=db)

            # default values used for running MOVES, actual VMT later used in save_data to compute total emission
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

                command = 'cd {moves_folder} & setenv.bat & ' \
                          'java -Xmx512M gov.epa.otaq.moves.master.commandline.MOVESCommandLine -r {run_moves}' \
                          ''.format(moves_folder=self.path_moves, run_moves=batch_run_dict[feed])
                os.system(command)

                # @TODO: change to use subprocess so output can be logged; for some reason subprocess doesn't work with multiple batch files - it only executes setenv.bat but never gets to {runspec_moves}.bat
                # output = subprocess.Popen(batch_run_dict[feed], cwd=self.path_moves,
                #                           stdout=subprocess.PIPE).stdout.read()
                # logger.debug('Command line output: %s' % output)

                # also tried the following, which allowed both setenv.bat and {runspec_moves}.bat but the runspec threw an error related to jdbc:
                # output = subprocess.Popen(os.path.join(self.path_moves, 'setenv.bat') + '&' + batch_run_dict[feed], cwd=self.path_moves, stdout=subprocess.PIPE, shell=True).stdout.read()
                # logger.debug('Command line output: %s' % output)

                self.kvals['moves_scen_id'] = "{fips}_{crop}_{year}_{month}_{day}".format(fips=fips, crop=feed, day=config.get('moves_timespan')['d'][0], month=config.get('moves_timespan')['mo'][0], year=self.yr[feed])
                query_moves_metadata = """INSERT INTO {constants_schema}.moves_metadata(scen_id)
                                          VALUES ('{moves_scen_id}')
                                          ;""".format(**self.kvals)
                self.db.input(query_moves_metadata)
            else:
                # otherwise, report that MOVES run already complete
                logger.info('MOVES run already complete for feedstock: %s, fips: %s' % (feed, fips))

    def save_data(self, operation_dict, alloc):
        """
        Create and populate the schema with the emissions inventory.

        :param operation_dict: Dictionary containing each feedstock. Each feedstock contains a dictionary
        of harvest, non-harvest, and transport and whether to calculate them. dict(dict(boolean))
        :param alloc: non-harvest emission allocation factor
        """

        logger.info('Saving results to database')

        # init update database object (creates tables)
        update = UpdateDatabase.UpdateDatabase(cont=self.cont)

        # create tables for all feedstocks
        for feedstock in self.feedstock_list:
            update.create_tables(feedstock=feedstock)

        # post-process production data
        # get toggle for regional crop budget
        regional_crop_budget = config.get('regional_crop_budget')

        # post-process data to obtain emissions from on-farm operations (non-harvest; harvest; chemical and fertilizer)
        self.post_process_nonroad(operation_dict=operation_dict, alloc=alloc, regional_crop_budget=regional_crop_budget)  # NONROAD
        self.post_process_fert(regional_crop_budget=regional_crop_budget)  # fertilizer
        self.post_process_pest(regional_crop_budget=regional_crop_budget)  # pesticide
        self.post_process_aerial(operation_dict=operation_dict, alloc=alloc, regional_crop_budget=regional_crop_budget)  # aerial emissions from crop dusting
        self.post_process_on_farm_fugitive_dust()  # on-farm fugitive dust

        # perform single pass allocation when national crop budget is selected and all feedstocks are modeled
        if regional_crop_budget is False:
            self.single_pass_alloc()

        # post-process transportation/logistics
        # post-process data to obtain emissions from processing (processing, adv; processing, conv)
        self.post_process_logistics()  # logistics (pre-processing)

        # post-process data to obtain emissions from off-farm transportation (transporation, adv; transportation, conv)
        kvals = self.kvals
        kvals['yield'] = self.scenario_yield
        kvals['year'] = self.scenario_year

        feed_id_dict = config.get('feed_id_dict')

        for feedstock in self.feedstock_list:
            # set feedstock id
            kvals['feed'] = feed_id_dict[feedstock]

            # if feedstock does not equal none (i.e., there are transportation data for the feedstock)
            if kvals['feed'] != 'None':
                # calculate emissions from off-farm transportation
                self.post_process_off_farm_transport(feedstock=feedstock)

    def concat_zeros(self, table_name):
        """
        Pre-appends zeros to FIPS codes that are 4 characters in length
        :param table_name: name of table to which concatenation should be applied
        :return:
        """
        # get kvals dictionary
        kvals = self.kvals

        # set table name
        kvals['table_name'] = table_name

        # create query to pre-append zeros to FIPS codes of 4 characters in length
        query = """UPDATE {scenario_name}.{table_name}
                   SET FIPS = CONCAT('0', FIPS)
                   WHERE length(FIPS) = 4
                   ;""".format(**kvals)

        # execute query
        self.db.input(query)

    def post_process_off_farm_transport(self, feedstock):
        """
        Compute emissions from off-farm transportation

        :param feedstock: feedstock
        :return:
        """
        # set values in kvals dictionary for string formatting
        kvals = self.kvals
        kvals['year'] = self.scenario_year
        kvals['feed'] = feedstock.lower()
        kvals['feed_id'] = self.feed_id_dict[feedstock]
        kvals['silt_table'] = config.get('db_table_list')['silt_table']

        # now loop through logistics systems to compute respective transportation emissions
        for logistics_type in self.logistics_list:
            # set truck capacity
            truck_capacity = config.get('truck_capacity')
            kvals['truck_capacity'] = truck_capacity[feedstock][logistics_type]

            # set transport table
            kvals['transport_table'] = self.transport_table_dict[self.feed_type_dict[feedstock]][self.scenario_yield][logistics_type] + '_%s' % (self.scenario_year, )

            # get list of fips codes from transportation table
            query = """SELECT DISTINCT LPAD(sply_fips, 5, '0')
                       FROM {production_schema}.{transport_table}
                       WHERE feed_id = '{feed_id}'
                       ORDER BY LPAD(sply_fips, 5, '0')
                       ;""".format(**kvals)
            fips_list = list(self.db.output(query))[0]

            # loop through fips codes and calculate transportation emissions
            for i, fips in enumerate(fips_list):
                # set fips and state
                fips = str(fips[0])
                kvals['fips'] = fips
                kvals['state'] = fips[0:2]

                # check if scenario requires moves to run on state-level
                if self.moves_state_level is True:
                    for m_fips in self.moves_fips_list[0]:
                        if fips[0:2] in m_fips[0]:
                            moves_fips = m_fips[0]
                            break
                else:
                    # if not run on state-level, then moves is run on county-level so production fips equals moves_fips
                    moves_fips = fips

                if moves_fips is not None:  # @TODO: remove check or handle case when moves_fips is None
                    # set moves fips in kvals
                    kvals['moves_fips'] = moves_fips

                    logger.info('Processing off-farm transportation for feedstock: {feed}, fips: {fips}, moves_fips: {moves_fips}'.format(**kvals))

                    if i == 0:
                        # average speed distribution only needs to be generated once per fips
                        kvals['feedstock'] = list(self.moves_feedstock_list)[0]  # and for all crops, so just pick one feedstock from the list

                        # generate average speed table for MOVES data analysis by joining tables for average speed and "dayhour"
                        query = """DROP TABLE IF EXISTS {constants_schema}.averageSpeed;
                                   CREATE TABLE {constants_schema}.averageSpeed
                                   AS (SELECT table1.roadTypeID, table1.avgSpeedBinID, table1.avgSpeedFraction, table2.hourID, table2.dayID, table1.hourDayID
                                   FROM fips_{moves_fips}_{year}_{feedstock}_in.avgspeeddistribution table1
                                   LEFT JOIN {moves_database}.hourday table2
                                   ON table1.hourDayID = table2.hourDayID)
                                   ;""".format(**kvals)
                        self.db.create(query)

                    # query database to determine required population of trucks (i.e., number of trips)
                    query_pop = """SELECT used_qnty / {truck_capacity}
                                   FROM {production_schema}.{transport_table}
                                   WHERE feed_id = '{feed_id}' AND sply_fips = {fips}
                                   ;""".format(**kvals)
                    output_pop = self.db.output(query_pop)

                    # as long as the output population is not none, set population of short haul trucks equal to this value
                    pop_short_haul = 0
                    if output_pop is not None:
                        try:
                            pop_short_haul = output_pop[0][0][0]  # population of combination short-haul trucks (assume one per trip and only run MOVES for single trip)
                        except IndexError:
                            pass

                    # set the name of the transportation distance column depending on the logistics type
                    trans_col = self.transport_col[logistics_type]['dist']  # equals dist for conventional
                    if len(self.transport_col[logistics_type]) == 2:
                        trans_col += '+ %s' % (self.transport_col[logistics_type]['dist_2'], )  # equals dist + dist_2 for advanced

                    # set transportation column in kvals
                    kvals['trans_col'] = trans_col

                    # query database to get vehicle miles travelled per trip
                    query_vmt = """SELECT {trans_col}
                                   FROM {production_schema}.{transport_table}
                                   WHERE feed_id = '{feed_id}' AND sply_fips = {fips}
                                   ;""".format(**kvals)
                    output_vmt = self.db.output(query_vmt)

                    # as long as the output of vmt is not none, set vmt of short haul trucks equal to this value
                    vmt_short_haul = 0
                    if output_vmt is not None:
                        try:
                            vmt_short_haul = output_vmt[0][0][0]  # annual vehicle miles traveled by combination short-haul trucks
                        except IndexError:
                            pass

                    # query database to get local silt data
                    query_silt = """SELECT uprsm_pct_silt
                                    FROM {constants_schema}.{silt_table}
                                    WHERE st_fips = {state}
                                    ;""".format(**kvals)
                    output_silt = self.db.output(query_silt)

                    # as long as the silt output is not none, set silt equal to this value
                    if output_silt is not None:
                        try:
                            silt = output_silt[0][0][0]  # local silt content
                        except IndexError:
                            logger.error('no silt data found for state fips: {state} in {constants_schema}.{silt_table}'.format(**kvals))

                    # if population of trucks (i.e., number of trips) and vehicle miles travelled are both greater than zero, then post-process moves output to compute emissions
                    if pop_short_haul > 0 and vmt_short_haul > 0:
                        transportation = Transportation.Transportation(feed=feedstock, cont=self.cont, fips=fips, vmt=vmt_short_haul, pop=pop_short_haul,
                                                                       logistics_type=logistics_type, silt=silt, yield_type=self.scenario_yield, moves_fips=moves_fips)
                        transportation.calculate_transport_emissions()

        # concatenate zeros for fips codes less than 5 characters in length
        self.concat_zeros('transportation')

        # concatenate zeros for fips codes less than 5 characters in length
        self.concat_zeros('fugitive_dust')

    def post_process_fert(self, regional_crop_budget):
        """
        Calculate NH3 and NOX emissions from nitrogen fertilizer application

        Populate data in {feed}_nfert tables
        :param regional_crop_budget: toggle for whether to use regional crop budget
        :return:
        """
        # initialize fertilizer object
        fert = Fertilizer.Fertilizer(cont=self.cont)

        # calculate emissions
        for feedstock in self.feedstock_list:
            # check if regional crop budget should be used
            if regional_crop_budget is True:
                logger.info('Using regional crop budget for fertilizer')
                year_range = self.years_budget[feedstock]
                for yr in range(1, year_range + 1):
                    fert.regional_fert(feed=feedstock, yr=yr)
                    logger.info('Fertilizer emissions complete for feed: %s, year: %s' % (feedstock, yr, ))
            else:
                fert.set_fertilizer(feed=feedstock)
                logger.info('Using national crop budget for fertilizer')
                logger.info('Fertilizer emissions complete for feed: %s' % (feedstock, ))

            # concatenate zeros for fips codes less than 5 characters in length
            self.concat_zeros('%s_nfert' % (feedstock.lower(), ))

    def post_process_pest(self, regional_crop_budget):
        """
        Calculate VOC emissions from pesticide application
        Populate data in {feed}_chem tables
        :param regional_crop_budget: toggle for whether to use regional crop budget
        :return:
        """
        # initialize chemical object
        chem = Chemical.Chemical(cont=self.cont)

        for feedstock in self.feedstock_list:
            if regional_crop_budget is True:
                logger.info('Using regional crop budget for chemicals')
                year_range = self.years_budget[feedstock]
                for yr in range(1, year_range + 1):
                    chem.regional_chem(feed=feedstock, yr=yr)
                    logger.info('Chemical emissions complete for feed: %s, year: %s' % (feedstock, yr, ))
            else:
                chem.set_chemical(feed=feedstock)
                logger.info('Using national crop budget for chemicals')
                logger.info('Chemical emissions complete for feed: %s' % (feedstock, ))

            # concatenate zeros for fips codes less than 5 characters in length
            self.concat_zeros('%s_chem' % (feedstock.lower(), ))

    def post_process_nonroad(self, operation_dict, alloc, regional_crop_budget):
        """
        Populate combustion emissions from NONROAD equipment
        Populate data in {feed}_raw tables

        :param regional_crop_budget: toggle for whether to use regional crop budget
        :param operation_dict: dictionary of operations
        :param alloc: non-harvest emission allocation factor
        :return:
        """

        # initialize database object
        comb = CombustionEmissions.CombustionEmissions(cont=self.cont, operation_dict=operation_dict, alloc=alloc, regional_crop_budget=regional_crop_budget)

        logger.info("Populating tables with combustion emissions")
        comb.populate_tables(run_codes=self.run_codes)
        logger.info("COMPLETED populating tables with combustion emissions")

        # concatenate zeros for fips codes less than 5 characters in length
        for feedstock in self.feedstock_list:
            self.concat_zeros('%s_raw' % (feedstock.lower(), ))

    def post_process_aerial(self, operation_dict, alloc, regional_crop_budget):
        """
        Populate emissions generated by crop dusting
        Populate data in aerial table

        :param regional_crop_budget: toggle for whether to use regional crop budget
        :param operation_dict: dictionary of operations
        :param alloc: non-harvest emission allocation factor
        :return:
        """
        comb = CombustionEmissions.CombustionEmissions(cont=self.cont, operation_dict=operation_dict, alloc=alloc, regional_crop_budget=regional_crop_budget)

        if regional_crop_budget is True:
            for run_code in self.run_codes:
                # only run for harvest activities associated with CG
                if run_code.startswith('CG') and run_code.endswith('N'):
                    comb.airplane_emission(run_code=run_code)

                    # concatenate zeros for fips codes less than 5 characters in length
                    # self.concat_zeros('cg_raw')

    def post_process_on_farm_fugitive_dust(self):
        """
        Calculate fugitive dust emissions associated with on-farm transport
        Populate under fug_pm10 and fug_pm25 columns in {feed}_raw tables

        :return:
        """

        fug_dust = FugitiveDust.FugitiveDust(cont=self.cont)

        for run_code in self.run_codes:
            if not (run_code.startswith('SG') or run_code.startswith('MS')):
                if not run_code.endswith('L'):
                    fug_dust.set_emissions(run_code=run_code)
                    logger.info("On-Farm Fugitive Dust Emissions complete for %s" % (run_code, ))
            elif run_code.startswith('SG'):
                if not run_code.endswith('L'):
                    sgfug_dust = FugitiveDust.SG_FugitiveDust(cont=self.cont, run_code=run_code)
                    sgfug_dust.set_emissions()
            elif run_code.startswith('MS'):
                if not run_code.endswith('L'):
                    msfug_dust = FugitiveDust.MSFugitiveDust(cont=self.cont, run_code=run_code)
                    msfug_dust.set_emissions()

    def single_pass_alloc(self):
        """
        Perform single pass allocation for emissions generated by the production of agricultural residues

        :return:
        """
        # allocate emissions for single pass methodology - see constructor for ability to allocate CG emissions
        logger.info("Allocate single pass emissions between corn stover and wheat straw")
        SinglePassAllocation.SinglePassAllocation(cont=self.cont)

    def nei_comparison(self):
        """
        Sum all emissions and compare to NEI data

        :return:
        """

        nei = NEIComparison.NEIComparison(cont=self.cont)

        # create a single table that has all emissions in this inventory
        logger.info('populating Summed Dimensions table')
        for feedstock in self.feedstock_list:
            nei.create_summed_emissions_table(feedstock=feedstock)

        # create tables that contain a ratio to NEI
        for count, feedstock in enumerate(self.feedstock_list):
            nei.create_nei_comparison(feedstock=feedstock)
            if count == len(self.feedstock_list):
                # on the last go, make a total query for all cellulosic.
                nei.create_nei_comparison(feedstock='cellulosic')

    def post_process_logistics(self):
        """
        Compute emissions and electricity associated with feedstock logistics
        Does not perform calculations for all feedstock types (only those specified under the feed_id_dict in the config file
        Populates data in {feed}_processing tables

        :return:
        """

        logistics = Logistics.Logistics(feedstock_list=self.feedstock_list, cont=self.cont)
        logistics.calc_logistics(logistics_list=self.logistics_list)

        # concatenate zeros for fips codes less than 5 characters in length
        self.concat_zeros('processing')

    def figure_plotting(self):
        """
        Create graphics and numerical summary

        :return:
        """

        self.nei_comparison()

        # Contribution Analysis
        logger.info('Creating emissions contribution figure')
        ContributionFigure.ContributionAnalysis(cont=self.cont)

        # Emissions Per Gallon
        logger.info('Creating emissions per gallon figure')
        EmissionsPerGalFigure.EmissionsPerGallon(cont=self.cont)

        # Emissions per a acre figure.
        logger.info('Creating emissions per acre figure')
        EmissionsPerAcreFigure(cont=self.cont)

        # Emissions per a production lb figure.
        logger.info('Creating emissions per lb figure')
        EmissionPerProdFigure(cont=self.cont)

        # Ratio to NEI
        RatioToNEIFigure.RatioToNEIFig(cont=self.cont)

if __name__ == '__main__':
    raise NotImplementedError
