"""Executes FPEAM against given datasets and configuration files."""

import argparse
import os

from FPEAM import (Data, IO, FPEAM)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Execute FPEAM model against a given equipment'
                    ' budget and production'
                    ' dataset and configuration files')

    parser.add_argument('budget', type=str, help='equipment budget')
    parser.add_argument('production', type=str, help='production data')
    parser.add_argument('run_config', type=str, help='execution configuration')

    data_group = parser.add_argument_group('data files')
    data_group.add_argument('--emission_factors', type=str,
                            default='../data/emission_factors.csv',
                            help='emission factor values')
    data_group.add_argument('--fertilizer_distribution', type=str,
                            default='../data/fertilizer_distribution.csv',
                            help='fertilzer distribution percentage values')
    data_group.add_argument('--fugitive_dust', type=str,
                            default='../data/fugitive_dust_emission_factors.csv',
                            help='fugitive dust emission factors values')

    config_group = parser.add_argument_group('configuration files')
    config_group.add_argument('--fpeam_config', type=str,
                              default='../configs/fpeam.ini',
                              help='FPEAM model configuration options')
    config_group.add_argument('--moves_config', type=str,
                              default='../configs/moves.ini',
                              help='MOVES model configuration options')
    config_group.add_argument('--nonroad_config', type=str,
                              default='../configs/nonroad.ini',
                              help='NONROAD configuration options')
    config_group.add_argument('--chemical_config', type=str,
                              default='../configs/chemical.ini',
                              help='chemical module configuration options')
    config_group.add_argument('--fugitivedust_config', type=str,
                              default='../configs/fugitivedust.ini',
                              help='fugitive dust module configuration options')

    args = parser.parse_args()

    for _arg in [arg[1] for arg in args._get_kwargs()]:
        try:
            assert os.path.exists(_arg)
        except AssertionError:
            raise RuntimeError(
                '{} does not exist; verify path'.format(os.path.abspath(_arg)))

    _budget = Data.Budget(fpath=args.budget)
    _production = Data.Production(fpath=args.production)
    _config = IO.load_config(args.fpeam_config,
                             args.moves_config,
                             args.nonroad_config,
                             args.chemical_config,
                             args.fugitivedust_config,
                             args.run_config)

    _fpeam = FPEAM(budget=_budget, production=_production, run_config=_config)

    _fpeam.execute()
