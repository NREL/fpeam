"""Input and output helper utilties."""

import sys

import pandas as pd


def load_config(*fpath):
    """
    Load config file.

    :param fpath: [string] INI file path
    :return: [configObj]
    """
    import configobj
    import validate

    # set file paths
    _config_fpaths = set(
            ['../fpeam.ini', '../database.ini', '../moves.ini', '../nonroad.ini'] + list(fpath)
            + ['../local.ini', ])
    _cspec_fpath = '../config.spec'

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
                _msg = 'Invalid keys in section {}: {}'.format(_key, ', '.join(_section_list))
            else:
                _msg = 'Missing sections: {} '.format(', '.join(_section_list))
            print(_msg)
        print('Check configuration file(s) for errors')

        sys.exit('invalid config file(s): {}'.format(_config_fpaths))
    else:
        return _config


def load(fpath, columns, memory_map=True, header=0, **kwargs):
    """
    Load data from a text file at <fpath>.

    See pandas.read_table() help for additional arguments.

    :param fpath: [string] file path to budget file or SQLite database file
    :param columns: [dict] {name: type, }
    :param memory_map: [bool] load directly to memory for improved performance
    :param header: [int] 0-based row index containing column names
    :return: [DataFrame]
    """
    _names = kwargs.get('names', columns.keys())

    return pd.read_table(filepath_or_buffer=fpath, sep=',', names=_names, dtype=columns,
                         usecols=columns.keys(),  memory_map=memory_map, header=header)
