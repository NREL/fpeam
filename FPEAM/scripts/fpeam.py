"""Executes FPEAM against given datasets and configuration files."""

import argparse
import os

from FPEAM import (Data, IO, FPEAM)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Execute FPEAM model against a given equipement'
                    ' budget and production'
                    ' dataset and configuration file')

    parser.add_argument('budget', type=str, help='equipment budget')
    parser.add_argument('production', type=str, help='production data')
    parser.add_argument('run_config', type=str, help='execution configuration')

    parser.add_argument('--fpeam_config', type=str,
                        default='../configs/fpeam.ini',
                        help='FPEAM model configuration options')
    parser.add_argument('--moves_config', type=str,
                        default='../configs/moves.ini',
                        help='MOVES model configuration options')
    parser.add_argument('--nonroad_config', type=str,
                        default='../configs/nonroad.ini',
                        help='NONROAD configuration options')
    parser.add_argument('--chemical_config', type=str,
                        help='chemical module configuration options')
    parser.add_argument('--fugitivedust_config', type=str,
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
