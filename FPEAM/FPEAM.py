import os
from collections import Iterable
from pkg_resources import resource_filename
import pandas as pd

from . import Data
from FPEAM import EngineModules
from . import utils
from .IO import (CONFIG_FOLDER, load_configs)

LOGGER = utils.logger(name=__name__)


class FPEAM(object):
    """Base class to hold shared information"""

    __version__ = '2.0.1-beta'

    # @TODO: can't these be discovered via the Modules module?
    MODULES = {'emissionfactors': EngineModules.EmissionFactors,
               'fugitivedust': EngineModules.FugitiveDust,
               'MOVES': EngineModules.MOVES,
               'NONROAD': EngineModules.NONROAD}

    def __init__(self, run_config):

        """
        :param run_config: [ConfigObj]
        """
        self._config = None

        self._modules = {}

        self._budget = None
        self._production = None

        self._emission_factors = None
        self._fertilizer_distribution = None
        self._fugitive_dust = None

        self.router = None

        # @TODO: load and validate fpeam.ini; currently only run_config gets checked and loaded
        self.config = run_config
        self.equipment = Data.Equipment(fpath=self.config['equipment']).reset_index().rename({'index': 'row_id'}, axis=1)
        self.production = Data.Production(fpath=self.config['production']).reset_index().rename({'index': 'row_id'}, axis=1)

        for _module in self.config.get('modules', None) or self.MODULES.keys():
            _config = run_config.get(_module.lower(), None) or \
                      load_configs(resource_filename('FPEAM', '%s/%s.ini' % (CONFIG_FOLDER, _module.lower()))
                                   )[_module.lower()]
            _config['scenario_name'] = _config.get('scenario_name', '').strip() or self.config['scenario_name']

            try:
                self.__setattr__(_module,
                                 FPEAM.MODULES[_module](config=_config,
                                                        equipment=self.equipment,
                                                        production=self.production))
            except KeyError:
                if _module not in FPEAM.MODULES.keys():
                    LOGGER.warning('invalid module name: {}.'
                                   ' Must be one of: {}'.format(_module,
                                                                FPEAM.MODULES.keys()))
                else:
                    raise
            except Exception:
                raise
            else:
                self._modules[_module] = self.__getattribute__(_module)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):

        _spec = resource_filename('FPEAM', '%s/run_config.spec' % (CONFIG_FOLDER, ))
        _config = utils.validate_config(config=value['run_config'], spec=_spec)
        if _config['extras']:
            LOGGER.warning('extra values: %s' % (_config['extras'], ))
        try:
            assert not _config['missing'] and not _config['errors']
        except AssertionError:
            if _config['missing']:
                LOGGER.error('missing values: %s' % (_config['missing'], ))
            if _config['errors']:
                LOGGER.error('invalid values: %s' % (_config['errors'], ))
            raise RuntimeError('Verify config file(s) are complete')
        else:
            self._config = _config['config']

    def run(self, modules=None):
        """
        Execute each Module in <module>.

        :param modules: [list] module classes with run() and save() methods
        :return: [dict] {<module>: <status>, ...}
        """

        if modules and not isinstance(modules, Iterable):
            modules = [modules, ]

        _results = {}

        for _module in modules or self._modules.values():
            LOGGER.info('running module: {}'.format(_module))
            _module.run()
            LOGGER.info('{}: {}'.format(_module, _module.status))
            # @TODO: add results/status details
            _results[_module] = _module.status

        self.results = self.collect(modules)


    def collect(self, modules=None):
        """
        Merge result sets.

        :param modules: [list] module classes with result property.\
        :return: [DataFrame]
        """

        _df = pd.DataFrame()

        # loop thru all modules being run and stack the data frames
        # containing output from each module
        # this will add empty values if a data frame is missing a column,
        # which does happend for some id variables from some modules
        for _module in modules or self._modules.values():
            _df = _df.append(_module.results,
                             ignore_index=True,
                             sort=False)

        _df['unit_numerator'] = 'lb pollutant'
        _df['unit_denominator'] = 'county-year'

        return _df

    def summarize(self):
        """
        summarization method called on the results dataframe created by the
        collect method

        :param modules:
        :return:
        """
        LOGGER.info('summarizing results')

        # feedstock-tillage type-region_production
        _summarize_by_region_production = self.results.groupby(['feedstock',
                                                                'tillage_type',
                                                                'region_production',
                                                                'pollutant'],
                                                               as_index=False).sum()

        _summarize_by_region_production['unit_numerator'] = 'lb pollutant'
        _summarize_by_region_production['unit_denominator'] = 'county-year'

        _summarize_by_region_production[['feedstock', 'tillage_type',
                                         'region_production', 'pollutant',
                                         'pollutant_amount',
                                         'unit_numerator',
                                         'unit_denominator']].to_csv(
            os.path.join(self.config['project_path'],
                         '%s' %
                         self.config['scenario_name'] +\
                         '_total_emissions_by_production_region.csv'),
            index=False)

        if 'region_transportation' in self.results.columns:
            # feedstock-tillage type-region_transportation
            _summarize_by_region_transportation = self.results.groupby(['feedstock',
                                                                        'tillage_type',
                                                                        'region_transportation',
                                                                        'pollutant'], as_index=False).sum()

            _summarize_by_region_transportation['unit_numerator'] = 'lb ' \
                                                                    'pollutant'
            _summarize_by_region_transportation['unit_denominator'] = \
                'transportation county-year'

            _summarize_by_region_transportation[['feedstock', 'tillage_type',
                                                 'region_transportation',
                                                 'pollutant',
                                                 'pollutant_amount']].to_csv(
                os.path.join(self.config['project_path'],
                             '%s' %
                             self.config['scenario_name'] +\
                             '_transportation_emissions_by_region.csv'),
                index=False)

        else:
            LOGGER.info('could not summarize by transportation region')

        # feedstock-tillage type-module
        _summarize_by_module = self.results.groupby(['feedstock',
                                                     'tillage_type',
                                                     'module',
                                                     'pollutant'],
                                                    as_index=False).sum()

        _summarize_by_module['unit_numerator'] = 'lb pollutant'
        _summarize_by_module['unit_denominator'] = 'county-year'

        _summarize_by_module[['feedstock', 'tillage_type', 'module',
                              'pollutant', 'pollutant_amount']].to_csv(
            os.path.join(self.config['project_path'],
                         '%s' %
                         self.config['scenario_name'] +\
                         '_total_emissions_by_module.csv'), index=False)

    def plot(self, modules):
        for _module in modules or self._modules.values():
            LOGGER.debug('plotting %s' % _module)

        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # process exceptions
        if exc_type is not None:
            LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self

    def __str__(self):
        return self.__name__
