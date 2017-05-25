import os

from AirPollution import utils
from model.Database import Database
from AirPollution.Driver import Driver
from AirPollution.FigurePlottingBT16 import FigurePlottingBT16
from LoadData import LoadData
import AirPollution.CleanTables as CleanTables


if __name__ == "__main__": 

    logger = utils.logger
    config = utils.config

    # exit if using invalidated parameters
    if config.as_bool('regional_crop_budget') is False:
        raise NotImplementedError('Non-regional budget crops are no longer supported')

    # get scenario title
    title = config.get('title')
    logger.info('Starting scenario %s' % (title, ))

    # get run codes
    run_codes = config.as_list('run_codes')
    logger.info('Processing run codes: %s' % (', '.join(run_codes, )))

    # load production data
    if config.as_bool('load_data') is True:
        logger.info('Loading production data')
        ld = LoadData(scenario_year=config.get('year_dict')['all_crops'], scenario_yield=config.get('yield'))
        ld.load_all_data()

    # create database
    logger.debug('Initializing database')
    db = Database(model_run_title=title)

    # init useless variable to pass around for no reason
    qprocess = None

    # get fertilizer distributions
    fert_dist = config['fert_dist']
    logger.debug('Fertilizer distribution: %s' % (fert_dist, ))

    # get fertilizer application for CS, WS, SG
    n_fert_app = config['n_fert_app']
    logger.debug('Fertilizer application: %s' % (n_fert_app, ))
    
    # get fertilizer emission factor (% volatilized)
    n_fert_ef = config['n_fert_ef']
    logger.debug('Emission factor (percent): %s' % (n_fert_ef, ))

    # get operation indicators
    operation_dict = config['operation_dict']
    logger.debug('Operation indicators: %s' % (operation_dict, ))

    # get non-harvest emission allocation values
    alloc = config['alloc']
    logger.debug('Non-harvest emission allocation: %s' % (alloc, ))

    # get list of scenario years by crop
    year_dict = config['year_dict']
    logger.debug('Scenario years: %s' % (year_dict, ))

    # get toggle for running moves on state level
    state_level_moves = config.as_bool('state_level_moves')
    if state_level_moves is True:
        logger.debug('Running moves on state level')

    fips_list = []
    if config.as_bool('run_moves') is True:
        # get list of FIPS codes for MOVES runs
        if config['moves_by_crop'] is False:
            crop = 'all_crops'
            fips_list = utils.get_fips(scenario_year=year_dict[crop], state_level_moves=state_level_moves, db=db, crop=crop)
        else:
            # need to be written to correctly get fips for each county by crop
            raise NotImplementedError('Not able to gather fips for MOVES by crop')

    # run air pollution program through command line
    logger.debug('Initializing driver')
    driver = Driver(model_run_title=title, run_codes=run_codes, year_dict=year_dict, db=db, moves_fips_list=fips_list)

    # setup and run moves for all fips in fips_list
    if config.as_bool('run_moves') is True:
        for fips in fips_list[0]:
            fips = fips[0]  # access first item in tuple because fips_list is returned from query as tuple [(fips1, ), (fips2, ), ...]
            # set up MOVES: create input data files, import data, generate run specs
            logger.debug('Setting up MOVES input files for fips: %s' % (fips, ))
            batch_run_dict = driver.setup_moves(fips=fips)
            # run MOVES
            logger.debug('Running MOVES for fips: %s' % (fips, ))
            driver.run_moves(batch_run_dict=batch_run_dict, fips=fips)

    if config.as_bool('post_process_index_moves_outputdb') is True:
        logger.info('Adding columns and indices to {d}'.format(d=config.get('moves_output_db')))
        driver.post_process_moves_output_db()

    regional_crop_budget = config.as_bool('regional_crop_budget')
    if regional_crop_budget is True:
        logger.debug('Setting up NONROAD input files with regional crop budget')
    else:
        logger.debug('Setting up NONROAD input files with national crop budget')

    if config.as_bool('setup_nonroad') is True:
        # set up NONROAD input files
        driver.setup_nonroad(regional_crop_budget=regional_crop_budget)

    if config.as_bool('run_nonroad') is True:
        # run NONROAD
        logger.info('Running NONROAD')
        driver.run_nonroad(qprocess)

    if config.as_bool('clean_moves'):
        CleanTables.main()

    if config.as_bool('save_nonroad_data') is True:
        # save the data from the NONROAD run to the database
        logger.info('Saving data')
        driver.save_data(operation_dict, alloc)

    # generate figures
    if config.as_bool('figure_plotting') is True:
        # # old figures
        # driver.figure_plotting()

        # new figures for BT16
        for data_type in ['produced', ]:  # @TODO: fix to run for both produced and delivered - currently only works for produced (generates correct output to total emissions table)
            FigPlot16 = FigurePlottingBT16(db=db, data_type=data_type)
            if config.as_bool('compile_results') is True:
                FigPlot16.compile_results()
            if (config.as_bool('plot_per_gal') is True) or (config.as_bool('plot_per_dt') is True):
                results = FigPlot16.get_data()
            if config.as_bool('plot_per_gal') is True:
                FigPlot16.plot_emissions_per_gal(emissions_per_dt_dict=results['emissions_per_dt'], filename='emissions_kg_per_gal_{data_type}.png'.format(data_type=data_type))
            if config.as_bool('plot_per_dt') is True:
                FigPlot16.plot_emissions_per_dt(emissions_per_dt_dict=results['emissions_per_dt'], filename='emissions_lbs_per_dt_{data_type}.png'.format(data_type=data_type))
            if config.as_bool('plot_contribution') is True:
                FigPlot16.contribution_figure(filename='contribution_{data_type}.png'.format(data_type=data_type))

    logger.info('Successful completion of model run')

    if config.as_bool('transfer_total_emissions') is True:

        kvals = {'src_host': config.get('db_host'),
                 'src_db': title,
                 'src_user': config.get('db_user'),
                 'src_pass': config.get('db_pass'),
                 'src_table': config.get('te_table_name'),
                 'fpath': os.path.join(config.get('project_path'), config.get('title'), '%s.sql' % (config.get('te_table_name'), )),
                 'dst_host': config.get('te_db_host'),
                 'dst_db': config.get('te_db_name'),
                 'dst_user': config.get('te_db_user'),
                 'dst_pass': config.get('te_db_pass'),
                 'dst_table': config.get('te_table_name'),
                 'mysql_binary': config.get('mysql_binary'),
                 'mysqldump_binary': config.get('mysqldump_binary')
                 }

        logger.info('Transferring total emissions data to {dst_db}.{dst_table} on {dst_host}'.format(**kvals))
        driver.transfer_total_emissions(**kvals)
