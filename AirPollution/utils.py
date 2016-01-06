import configobj
import os
import logging
import sys
import datetime
import getpass

# get current date
cdate = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# get configuration info
try:
    cfile = os.path.abspath(sys.argv[1])
except IndexError:
    cfile = os.path.abspath('config.ini')

try:
    dfile = os.path.abspath(sys.argv[2])
except IndexError:
    dfile = os.path.abspath('database.ini')

try:
    config = configobj.ConfigObj(cfile, file_error=True)
except (configobj.ConfigObjError, IOError), e:
    sys.exit('Error with config file {cfile}: {e}'.format(cfile=cfile, e=e))

try:
    d_config = configobj.ConfigObj(dfile, file_error=True)
except (configobj.ConfigObjError, IOError), e:
    sys.exit('Error with database config file {cfile}: {e}'.format(cfile=cfile, e=e))

try:
    config.merge(d_config)
except configobj.ConfigObjError, e:
    sys.exit('Error combining config files {cfile} and {dfile}: {e}'.format(cfile=cfile, e=e, dfile=dfile))


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
        if config.has_key('logging_level'):
            level = config.get('logging_level')
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
    log_file = '{u}_{f}_{d}.log'.format(u=getpass.getuser(), f=config.filename[:-4], d=cdate)
    handler = logging.FileHandler(os.path.join(output_dir, log_file), 'w', encoding=None, delay='true')
    handler.setLevel(log_levels[level])

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# create logger
logger = initialize_logger()

# log config file
logger.debug('Config file: %s' % os.path.abspath(config.filename))
