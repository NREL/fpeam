# populate DB from GUI or config file
# provide interface to the database

import sys
import os
import pandas as pd

# from sqlalchemy.engine import Engine
# from sqlalchemy import event
# from sqlalchemy import create_engine
# from sqlalchemy.exc import SQLAlchemyError

import Budget.HEADERS as BUDGET_HEADERS

# set default loaders


# @event.listens_for(Engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA foreign_keys=ON")
#     cursor.close()


def load_config(*fpath):
    """
    Load config file.

    :param fpath: [string] INI file path
    :return: [configObj]
    """

    import configobj
    import validate

    # set file paths
    _config_fpaths = ['fpeam.ini', 'database.ini', 'moves.ini', 'nonroad.ini'] + fpath + ['local.ini', ]
    _cspec_fpath = 'config.spec'

    # init config
    _config = configobj.ConfigObj({}, configspec=_cspec_fpath, file_error=True, unrepr=False)

    # load and add additional configs
    for _config_fpath in _config_fpaths:
        try:
            _config.merge(configobj.ConfigObj(_config_fpath))
        except (configobj.ConfigObjError, IOError):
            raise

    # init config validator
    _validator = validate.Validator()

    # validate config
    _validated_config = _config.validate(_validator)

    # if errors in config, log and exit
    if not _validated_config:
        for (_section_list, _key, _) in configobj.flatten_errors(_config, _validated_config):
            if _key is not None:
                _msg = 'The "%s" key in the section "%s" failed validation' % (_key, ', '.join(_section_list))
            else:
                _msg = 'The following section was missing: %s ' % ', '.join(_section_list)
            print(_msg)
        print 'Check configuration file(s) for errors'

        sys.exit('invalid config file(s): {}'.format(_config_fpaths))
    else:
        return _config


def load(fpath, columns, **kwargs):
    """
    Load data from a text file at <fpath>.

    See pandas.read_table() help for additional arguments.

    :param fpath: [string] file path to budget file or SQLite database file
    :param columns: [dict] {name: type, }
    :return: [DataFrame]
    """

    try:
        # verify file path
        assert os.path.exists(fpath)
    except AssertionError:
        raise IOError('{} is not a valid file path'.format(fpath))

    try:
        _names = kwargs['names']
    except KeyError:
        _names = columns.keys()

    return pd.read_table(filepath_or_buffer=fpath, names=_names, dtype=columns, usecols=columns.keys())
