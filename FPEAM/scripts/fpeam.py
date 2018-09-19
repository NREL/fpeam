"""Executes FPEAM against given datasets and configuration files."""

import argparse
import logging
import os
from datetime import datetime

from FPEAM import (IO, FPEAM, utils)


def main():
    parser = argparse.ArgumentParser(
        description='Execute FPEAM model against a given equipment'
                    ' group set and production'
                    ' dataset and configuration files')

    parser.add_argument('run_config', type=str, help='execution configuration')

    config_group = parser.add_argument_group('configuration files')
    config_group.add_argument('--moves_config', type=str,
                              default=None,
                              help='MOVES model configuration options')
    config_group.add_argument('--nonroad_config', type=str,
                              default=None,
                              help='NONROAD configuration options')
    config_group.add_argument('--emissionfactors_config', type=str,
                              default=None,
                              help='emission factors module configuration options')
    config_group.add_argument('--fugitivedust_config', type=str,
                              default=None,
                              help='fugitive dust module configuration options')

    run_group = parser.add_argument_group('run options')
    run_group.add_argument('-v', dest='verbose', action='store_true',
                           help='print more messages')
    run_group.add_argument('--l', '--log', dest='log', type=str,
                           default=os.path.abspath(os.path.join(os.path.curdir,
                                                                'fpeam_%s.log' %
                                                                (datetime.now().strftime('%Y%m%d_%H%M')))),
                           help='log file path (default: %(default)s')

    args = parser.parse_args()

    # create shared logger
    _logger = utils.logger(name=__name__)
    if args.verbose:
        logging.basicConfig(level='DEBUG', format='%(asctime)s, %(levelname)-8s'
                                                  ' [%(filename)s:%(module)s.'
                                                  '%(funcName)s.%(lineno)d] %(message)s',
                            filename=args.log,
                            filemode='w')

    # load config options
    _config = IO.load_configs(args.moves_config,
                              args.nonroad_config,
                              args.emissionfactors_config,
                              args.fugitivedust_config,
                              args.run_config)

    _fpeam = FPEAM(run_config=_config)

    _fpeam.run()

    _fpeam.results.to_csv(os.path.join(_fpeam.config['project_path'],
                                       '%s.csv' %
                                       _fpeam.config['scenario_name']),
                          index=False)


if __name__ == '__main__':
    main()
