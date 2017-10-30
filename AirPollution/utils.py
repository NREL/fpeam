import configobj, validate
import os
import logging
import sys
import datetime
import getpass

# get current date
cdate = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# get scenario configuration info from first command-line argument if provided, otherwise use default
try:
    cfile = os.path.abspath(sys.argv[1])
except IndexError:
    cfile = os.path.abspath('config.ini')

# get database configuration info from second command line argument if provided, otherwise use default
try:
    dfile = os.path.abspath(sys.argv[2])
except IndexError:
    dfile = os.path.abspath('database.ini')

# get scenario config
sfile = os.path.abspath('scenario.ini')

# get local config overrides
if os.path.exists('local.ini') is True:
    lfile = os.path.abspath('local.ini')

# set config specification file for validating
cspec_file = os.path.abspath('configspec.ini')

# load main config
try:
    config = configobj.ConfigObj(cfile, configspec=cspec_file, file_error=True)
except (configobj.ConfigObjError, IOError), e:
    print('Config error: %s' % (e, ))
    # if configobj fails to load the main config file, try a variation
    try:
        cfile = os.path.abspath(os.path.join('.', 'config.ini'))
        dfile = os.path.abspath(os.path.join('.', 'database.ini'))
        sfile = os.path.abspath(os.path.join('.', 'scenario.ini'))
        if os.path.exists(os.path.join('.', 'local.ini')) is True:
            lfile = os.path.abspath(os.path.join('.', 'local.ini'))
        cspec_file = os.path.abspath(os.path.join('.', 'configspec.ini'))

        config = configobj.ConfigObj(cfile, configspec=cspec_file, file_error=True)
    except Exception, e:
        sys.exit(e)

# bundle configs
config_fpaths = [dfile, sfile]
try:
    config_fpaths.append(lfile)
except:
    pass

# load secondary configs
configs = []
for config_fpath in config_fpaths:
    try:
        configs.append(configobj.ConfigObj(config_fpath, file_error=True))
    except (configobj.ConfigObjError, IOError), e:
        sys.exit('Error loading %s: %s' % (config_fpath, e))

# merge configs
for con in configs:
    try:
        config.merge(con)
    except configobj.ConfigObjError, e:
        sys.exit('Error combining config file: {c}: {e}'.format(c=con, e=e))

# validate config against cspec_file
validator = validate.Validator()
valid_config = config.validate(validator)

# if errors in config, log and exit
if valid_config is not True:
    for (section_list, key, _) in configobj.flatten_errors(config, valid_config):
        if key is not None:
            print 'The "%s" key in the section "%s" failed validation' % (key, ', '.join(section_list))
        else:
            print 'The following section was missing: %s ' % ', '.join(section_list)
    sys.exit('Check configuration file(s) for errors')


def initialize_logger(output_dir=os.getcwd(), level=None, file_log_level='DEBUG'):
    """
    Returns ready-to-use logger object.

    :param output_dir: directory to save log.
    :param level: verbosity level. One of CRITICAL, ERROR, WARNING, INFO, DEBUG. Defaults to config's logging level, then INFO.
    :return: main logger object.
    """

    # @TODO: allow separate levels for console and file handlers

    log_levels = {'CRITICAL': logging.CRITICAL,
                  'ERROR': logging.ERROR,
                  'WARNING': logging.WARNING,
                  'INFO': logging.INFO,
                  'DEBUG': logging.DEBUG}

    # set level if not already specified as a parameter or in the config
    if level is None:
        if config.has_key('logger_level'):
            level = config.get('logger_level')
        else:
            level = 'INFO'

    logger = logging.getLogger('main')
    logger.setLevel(log_levels[level])

    # create console handler and set level
    handler = logging.StreamHandler()
    handler.setLevel(log_levels[level])

    formatter = logging.Formatter('%(levelname)s - %(asctime)s -  %(funcName)s - %(lineno)d - Msg: "%(message)s"')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # create error file handler
    config_root = os.path.dirname(config.filename)
    _ = {'u': getpass.getuser(),
         'f': os.path.splitext(os.path.basename(config.filename))[0],
         'd': cdate}

    log_file = os.path.join(config_root, '{f}_{u}_{d}.log'.format(**_))
    handler = logging.FileHandler(os.path.join(output_dir, log_file), 'w', encoding=None, delay='true')
    handler.setLevel(log_levels[file_log_level])

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_fips(scenario_year, state_level_moves, db, crop):
    """
    Collect list of county FIPS codes.
    Create table to map MOVES fips to state

    :param scenario_year: year of scenario analysis
    :param state_level_moves: toggle for running MOVES on state-level (True) versus county-level (False)
    :param db: database object
    :param crop: name of crop to be run for MOVES (currently only works for all_crops)
    :return: [<FIPS>]
    """

    moves_timespan = config['moves_timespan']

    kvals = {'production_schema': config['production_schema'],
             'constants_schema': config['constants_schema'],
             'year': scenario_year,
             'yield': config.get('yield'),
             'month': moves_timespan['mo'][0],
             'day': moves_timespan['d'][0],
             'crop': crop,
             }

    if state_level_moves is True:
        query = """ DROP TABLE IF EXISTS {production_schema}.prod;
                    CREATE TABLE {production_schema}.prod
                    AS (SELECT total_prod as 'prod', LEFT(fips, 2) as state, fips, 'ms' as 'crop'
                    FROM {production_schema}.ms_data_{yield}_{year}
                    WHERE  total_prod > 0)

                    UNION
                    (SELECT total_prod as 'prod', LEFT(fips, 2) as state, fips, 'sg'
                    FROM {production_schema}.sg_data_{yield}_{year}
                    WHERE  total_prod > 0)

                    UNION
                    (SELECT IFNULL(prod,0) as prod, LEFT(fips,2) as state, fips,  'cg'
                    FROM {production_schema}.herb_{yield}_{year}
                    WHERE (crop = 'Corn') AND prod > 0)

                    UNION
                    (SELECT IFNULL(prod,0) as prod, LEFT(fips,2) as state, fips, 'cs'
                    FROM {production_schema}.herb_{yield}_{year}
                    WHERE (crop = 'Corn stover') AND prod > 0)

                    UNION
                    (SELECT IFNULL(prod,0) as prod, LEFT(fips,2) as state, fips, 'ws'
                    FROM {production_schema}.herb_{yield}_{year}
                    WHERE (crop = 'Wheat straw') AND prod > 0)

                    UNION
                    (SELECT IFNULL(prod,0) as prod, LEFT(fips,2) as state, fips, 'ws'
                    FROM {production_schema}.herb_{yield}_{year}
                    WHERE (crop = 'Sorghum stubble') AND prod > 0)

                    UNION
                    (SELECT IFNULL(total_prod,0) as prod, LEFT(fips,2) as state, fips, 'fr'
                    FROM {production_schema}.fr_data_{yield}_{year}
                    WHERE total_prod > 0)

                    UNION
                    (SELECT IFNULL(total_prod,0) as prod, LEFT(fips,2) as state, fips, 'fw'
                    FROM {production_schema}.fw_data_{yield}_{year}
                    WHERE total_prod > 0)
                    ;

                    ALTER TABLE {production_schema}.prod ADD INDEX (prod);
                    ALTER TABLE {production_schema}.prod ADD INDEX (state);
                    ALTER TABLE {production_schema}.prod ADD INDEX (fips);
                    ALTER TABLE {production_schema}.prod ADD INDEX (crop);
                    ALTER TABLE {production_schema}.prod ADD INDEX (fips, state);

                    DROP TABLE IF EXISTS {production_schema}.summed_prod;
                    CREATE TABLE {production_schema}.summed_prod
                    SELECT fips, state, sum(prod) as 'summed_prod'
                    FROM {production_schema}.prod
                    GROUP BY fips, state;

                    ALTER TABLE {production_schema}.summed_prod ADD INDEX (summed_prod);
                    ALTER TABLE {production_schema}.summed_prod ADD INDEX (state);
                    ALTER TABLE {production_schema}.summed_prod ADD INDEX (fips);

                    """.format(**kvals)
        db.create(query)

        query_moves_fips = """DROP TABLE IF EXISTS {constants_schema}.moves_statelevel_fips_list_{year};
                              CREATE TABLE {constants_schema}.moves_statelevel_fips_list_{year}
                              SELECT sum.fips, CONCAT(sum.fips, '_{crop}_{year}_{month}_{day}') AS MOVESScenarioID, sum.state
                              FROM (SELECT state, max(summed_prod) AS max_sum
                                    FROM {production_schema}.summed_prod
                                    GROUP BY state) summed_max
                              LEFT JOIN (SELECT fips, state, SUM(prod) AS 'summed_prod'
                                         FROM {production_schema}.prod
                                         WHERE prod > 0
                                         GROUP BY fips, state) sum
                              ON sum.summed_prod <= summed_max.max_sum + 0.1 and sum.summed_prod >= summed_max.max_sum - 0.1;

                              ALTER TABLE {constants_schema}.moves_statelevel_fips_list_{year} ADD INDEX idx_MOVESScenarioID (MOVESScenarioID);
                              ALTER TABLE {constants_schema}.moves_statelevel_fips_list_{year} ADD INDEX idx_state (state);
                              ALTER TABLE {constants_schema}.moves_statelevel_fips_list_{year} ADD INDEX idx_fips (fips);

                              ;""".format(**kvals)

        query_get = """SELECT fips
                       FROM {constants_schema}.moves_statelevel_fips_list_{year};""".format(**kvals)

        db.create(query_moves_fips)
        fips_list = db.output(query_get)

    else:
        # @TODO: replace with actual list of FIPS codes for run (probably use database table)
        fips_list = [(("01029", ), ), ]
        logger.warning('Query for county-level MOVES fips codes not written - only running for single FIPS')

    return fips_list

# create logger
logger = initialize_logger()

# log config file
logger.debug('Config file: %s' % os.path.abspath(config.filename))
