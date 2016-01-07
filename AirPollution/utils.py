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


def initialize_logger(output_dir=os.getcwd(), level=None):
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
    handler.setLevel(log_levels[level])

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# create logger
logger = initialize_logger()

# log config file
logger.debug('Config file: %s' % os.path.abspath(config.filename))
