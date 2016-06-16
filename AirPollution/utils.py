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

# get database configuration info from second command line argument if provided, otherwuse use default
try:
    dfile = os.path.abspath(sys.argv[2])
except IndexError:
    dfile = os.path.abspath('database.ini')

# set config specification file for validating
cspec_file = os.path.abspath('configspec.ini')

# load scenario config
try:
    config = configobj.ConfigObj(cfile, configspec=cspec_file, file_error=True)
except (configobj.ConfigObjError, IOError), e:
    sys.exit(e)

# load database config
try:
    d_config = configobj.ConfigObj(dfile, file_error=True)
except (configobj.ConfigObjError, IOError), e:
    sys.exit(e)

# merge configs
try:
    config.merge(d_config)
except configobj.ConfigObjError, e:
    sys.exit('Error combining config files {cfile} and {dfile}: {e}'.format(cfile=cfile, e=e, dfile=dfile))

# init config validator
validator = validate.Validator()
# validate config against cspec_file
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

    # @TODO: allow seperate levels for console and file handlers

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
    # logger.setLevel(log_levels[level])

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


def get_fips(scenario_year, state_level_moves, db):
    """
    Collect list of county FIPS codes.

    :param scenario_year: year of scenario analysis
    :param state_level_moves: toggle for running MOVES on state-level (True) versus county-level (False)
    :param db: database object
    :return: [<FIPS>]
    """
    kvals = {'production_schema': config['production_schema'],
             'year': scenario_year,
             'yield': config.get('yield')}

    if state_level_moves is True:
        query = """ DROP TABLE IF EXISTS {production_schema}.prod;
                    CREATE TABLE {production_schema}.prod
                    AS (SELECT total_prod as 'prod', LEFT(fips, 2) as state, fips, 'ms' as 'crop'
                    FROM {production_schema}.ms_data_{yield}_{year}
                    WHERE  total_prod > 0)

                    UNION
                    SELECT total_prod as 'prod', LEFT(fips, 2) as state, fips, 'sg'
                    FROM {production_schema}.sg_data_{yield}_{year}
                    WHERE  total_prod > 0

                    UNION
                    SELECT IFNULL(prod,0) as prod, LEFT(fips,2) as state, fips,  'cg'
                    FROM {production_schema}.herb_{yield}_{year}
                    WHERE (crop = 'Corn') AND prod > 0

                    UNION
                    SELECT IFNULL(prod,0) as prod, LEFT(fips,2) as state, fips, 'cs'
                    FROM {production_schema}.herb_{yield}_{year}
                    WHERE (crop = 'Corn stover') AND prod > 0

                    UNION
                    SELECT IFNULL(prod,0) as prod, LEFT(fips,2) as state, fips, 'ws'
                    FROM {production_schema}.herb_{yield}_{year}
                    WHERE (crop = 'Wheat straw') AND prod > 0

                    UNION
                    SELECT IFNULL(prod,0) as prod, LEFT(fips,2) as state, fips, 'ws'
                    FROM {production_schema}.herb_{yield}_{year}
                    WHERE (crop = 'Sorghum stubble') AND prod > 0;

                    DROP TABLE IF EXISTS {production_schema}.summed_prod;
                    CREATE TABLE {production_schema}.summed_prod
                    SELECT fips, state, sum(prod) as 'summed_prod'
                    FROM {production_schema}.prod
                    GROUP BY fips, state;""".format(**kvals)

        query_get = """ SELECT sum.fips
                        FROM
                        (SELECT state, max(summed_prod) as max_sum
                        FROM {production_schema}.summed_prod
                        GROUP by state) summed_max
                        LEFT JOIN (SELECT fips, state, sum(prod) as 'summed_prod'
                        FROM {production_schema}.prod
                        WHERE prod > 0
                        GROUP BY fips) sum ON summed_max.max_sum = sum.summed_prod;""".format(**kvals)

        db.create(query)
        fips_list = db.output(query_get)

    else:
        # @TODO: replace with actual list of FIPS codes for run (probably use database table)
        fips_list = [(("01029", ), ), ]

    return fips_list

# create logger
logger = initialize_logger()

# log config file
logger.debug('Config file: %s' % os.path.abspath(config.filename))
