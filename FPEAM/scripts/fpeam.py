"""Executes FPEAM against given datasets and configuration files."""

import argparse
import logging
import os

from FPEAM import (Data, IO, FPEAM, utils)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Execute FPEAM model against a given equipment'
                    ' group set and production'
                    ' dataset and configuration files')

    parser.add_argument('run_config', type=str, help='execution configuration')

    config_group = parser.add_argument_group('configuration files')
    config_group.add_argument('--fpeam_config', type=str,
                              default=None,
                              help='FPEAM application configuration options')
    config_group.add_argument('--moves_config', type=str,
                              default=None,
                              help='MOVES model configuration options')
    config_group.add_argument('--nonroad_config', type=str,
                              default=None,
                              help='NONROAD configuration options')
    config_group.add_argument('--chemical_config', type=str,
                              default=None,
                              help='chemical module configuration options')
    config_group.add_argument('--fugitivedust_config', type=str,
                              default=None,
                              help='fugitive dust module configuration options')

    run_group = parser.add_argument_group('run options')
    run_group.add_argument('-v', dest='verbose', action='store_true',
                           help='print messages')

    args = parser.parse_args()

    # validate file paths
    for _arg in [arg[1] for arg in args._get_kwargs()]:
        if isinstance(_arg, str):
            try:
                assert os.path.exists(_arg)
            except AssertionError:
                raise RuntimeError(
                    '{} does not exist; verify path'.format(os.path.abspath(_arg)))

    # create shared logger
    _logger = utils.logger(name=__name__)
    if args.verbose:
        logging.basicConfig(level='DEBUG', format='%(asctime)s, %(levelname)-8s'
                                                  ' [%(filename)s:%(module)s.'
                                                  '%(funcName)s.%(lineno)d] %(message)s')

    # load config options
    _config = IO.load_configs(args.moves_config,
                              args.nonroad_config,
                              args.chemical_config,
                              args.fugitivedust_config,
                              args.run_config)

    _fpeam = FPEAM(run_config=_config)

    _results = _fpeam.run()

    for _result in _results:
        _logger.info(_result)
