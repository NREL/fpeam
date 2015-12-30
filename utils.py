import configobj
import os
import logging
import sys
import datetime


# get current date
cdate = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# get configuration info
if len(sys.argv) > 1:
    config = configobj.ConfigObj(os.path.abspath(sys.argv[1]))
else:
    config = configobj.ConfigObj(os.path.abspath('config.ini'))


def initialize_logger(output_dir=os.getcwd(), level=None):
    """
    Returns ready-to-use logger object.

    :param output_dir: directory to save log.
    :param level: verbosity level. One of CRITICAL, ERROR, WARNING, INFO, DEBUG. Defaults to config's logging level, then INFO.
    :return: main logger object.
    """

    # @TODO: would like to be able to set seperate levels for console and file handlers

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
    handler = logging.FileHandler(os.path.join(output_dir, '%s_%s.log' % (config.filename[:-4], cdate)), 'w', encoding=None, delay='true')
    handler.setLevel(log_levels[level])

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# create logger
logger = initialize_logger()

# log config file
logger.debug('Config file: %s' % os.path.abspath(config.filename))
