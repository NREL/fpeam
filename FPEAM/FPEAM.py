import os
from collections import Iterable

from . import Data
from . import Modules
from . import utils
from .IO import (CONFIG_FOLDER, load_configs)

LOGGER = utils.logger(name=__name__)


class FPEAM(object):
    """Base class to hold shared information"""

    # @TODO: can't these be discovered via the Modules module?
    MODULES = {'emissionfactors': Modules.EmissionFactors,
               'fugitivedust': Modules.FugitiveDust,
               'MOVES': Modules.MOVES,
               'NONROAD': Modules.NONROAD}

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

        # @TODO: load and validate fpeam.ini; currently only run_config gets checked and loaded
        self.config = run_config
        self.router = None

        self.equipment = Data.Equipment(fpath=self.config['equipment']).reset_index().rename({'index': 'row_id'}, axis=1)
        self.production = Data.Production(fpath=self.config['production']).reset_index().rename({'index': 'row_id'}, axis=1)

        for _module in self.config.get('modules', None) or self.MODULES.keys():
            _config = run_config.get(_module.lower(), None) or \
                      load_configs(os.path.join(CONFIG_FOLDER, '%s.ini' % _module.lower())
                                   )[_module.lower()]

            _config = utils.validate_config(config=_config
                                            , spec=os.path.join(CONFIG_FOLDER
                                                                , '%s.spec' % _module.lower())
                                            )['config']
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

        _spec = os.path.join(CONFIG_FOLDER, 'run_config.spec')
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

        return _results

    def summarize(self, modules):

        for _module in modules or self._modules.values():
            LOGGER.debug('summarizing %s' % _module)

        raise NotImplementedError

    def plot(self, modules):
        for _module in modules or self._modules.values():
            LOGGER.debug('plotting %s' % _module)

        raise NotImplementedError

    def to_csv(self, modules):
        for _module in modules or self._modules.values():
            LOGGER.debug('exporting %s' % _module)

        raise NotImplementedError

    def to_sql(self, modules):
        for _module in modules or self._modules.values():
            LOGGER.debug('exporting %s' % _module)

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
