"""Input and output helper utilties."""

import os
from . import utils

import pandas as pd

CONFIG_FOLDER = os.path.join('..', 'configs')
DATA_FOLDER = os.path.join('..', 'data')
LOGGER = utils.logger(name=__name__)


def load_configs(*fpath):
    """
    Load and validate config file(s).

    'local.ini' is always loaded last, unless supplied in <fpath>.

    :param fpath: [string] additional INI file path(s)
    :return: [configObj]
    """

    import configobj

    fpath = list(fpath)

    # add local config if available
    _local_fpath = os.path.join(CONFIG_FOLDER, 'local.ini')
    if os.path.exists(_local_fpath) and _local_fpath not in fpath:
        fpath.append(_local_fpath)

    # init config
    _config = configobj.ConfigObj({}, file_error=True, unrepr=False, stringify=False)

    # add additional configs
    for _config_fpath in [_fpath for _fpath in fpath if _fpath is not None]:
        try:
            LOGGER.debug('importing config file: %s' % (os.path.abspath(_config_fpath), ))
            _config.merge(configobj.ConfigObj(_config_fpath))
        except (configobj.ConfigObjError, IOError):
            raise

    return _config


def load(fpath, columns, memory_map=True, header=0, **kwargs):
    """
    Load data from a text file at <fpath>.

    See pandas.read_table() help for additional arguments.

    :param fpath: [string] file path to budget file or SQLite database file
    :param columns: [dict] {name: type, ...}
    :param memory_map: [bool] load directly to memory for improved performance
    :param header: [int] 0-based row index containing column names
    :return: [DataFrame]
    """

    try:
        LOGGER.debug('importing columns %s from %s' % (columns, os.path.abspath(fpath)))
        _df = pd.read_table(filepath_or_buffer=fpath, sep=',', dtype=columns,
                            usecols=columns.keys(), memory_map=memory_map, header=header, **kwargs)
    except ValueError as e:
        if e.__str__() == 'Usecols do not match names.':
            from collections import Counter
            _df = pd.read_table(filepath_or_buffer=fpath, sep=',', dtype=columns,
                                memory_map=memory_map, header=header, **kwargs)
            _df_columns = Counter(_df.columns)
            _cols = list(set(columns.keys()) - set(_df_columns))
            raise ValueError('%(f)s missing columns: %(cols)s' % (dict(f=fpath, cols=_cols)))
        # elif e.__str__.startswith('ValueError: could not convert'):
        #     raise e
        else:
            raise e
    else:
        return _df
