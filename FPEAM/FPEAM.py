from Engine import Engine
from collections import Iterable
import Data
import utils
import Modules
from IO import CONFIG_FOLDER
import os
LOGGER = utils.logger(name=__name__)


class FPEAM(object):
    """Base class to hold shared information"""

    # @TODO: can't these be discovered via the Modules module?
    MODULES = {'chemical': Modules.EmissionFactors,
               'fugitive_dust': Modules.FugitiveDust,
               'MOVES': Modules.MOVES,
               'NONROAD': Modules.NONROAD}

    def __init__(self, run_config):

        """
        :param budget: [DataFrame]
        :param production: [DataFrame]
        :param run_config: [ConfigObj]
        """

        self._modules = {}

        self._config = None
        # @TODO: load and validate fpeam.ini; currently only run_config gets checked and loaded
        self._budget = None
        self._production = None

        self._emission_factors = None
        self._fertilizer_distribution = None
        self._fugitive_dust = None
        self._moisture_content = None

        self.config = run_config

        self.equipment = Data.Equipment(fpath=self.config['equipment']).reset_index().rename({'index': 'row_id'}, axis=1)
        self.production = Data.Production(fpath=self.config['production']).reset_index().rename({'index': 'row_id'}, axis=1)

        # @TODO: not sure these should default to None, maybe better to break than silently load nothing
        self.emission_factors =\
            Data.EmissionFactor(fpath=self.config.get('emission_factors', None))
        self.fertilizer_distribution =\
            Data.FertilizerDistribution(fpath=self.config.get('fertilizer_distribution', None))
        self.fugitive_dust =\
            Data.FugitiveDust(fpath=self.config.get('fugitive_dust_emission_factors', None))
        self.moisture_content =\
            Data.MoistureContent(fpath=self.config.get('moisture_content', None))
        self.nonroad_equipment =\
            Data.NONROADEquipment(fpath=self.config.get('nonroad_equipment', None))
        self.ssc_codes = Data.SCCCodes(fpath=self.config.get('scc_codes', None))

        for _module in self.config['modules']:
            try:
                self.__setattr__(_module,
                                 FPEAM.MODULES[_module](config=run_config.get(_module, None),
                                                        equipment=self.equipment,
                                                        production=self.production,
                                                        emission_factors=self.emission_factors,
                                                        fertilizer_distribution=self.fertilizer_distribution,
                                                        fugitive_dust=self.fugitive_dust,
                                                        moisture_content=self.moisture_content))
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

    # self.Engine = Engine(budget=self.budget, production=self.production, config=self.config)

    # @property
    # def budget(self):
    #     return self._budget
    #
    # @budget.setter
    # def budget(self, value):
    #     try:
    #         assert Data.Budget.validate(value)
    #     except AssertionError:
    #         raise RuntimeError('{} failed validation: \n\n{}'.format('budget', value.head()))
    #     else:
    #         self._budget = Data.Budget(df=value)
    #
    # @property
    # def production(self):
    #     return self._production
    #
    # @production.setter
    # def production(self, value):
    #     try:
    #         assert Data.Production.validate(value)
    #     except AssertionError:
    #         raise RuntimeError('{} failed validation: \n\n{}'.format('production', value.head()))
    #     else:
    #         self._production = Data.Production(df=value)
    #
    # @property
    # def emission_factors(self):
    #     return self._emission_factors
    #
    # @emission_factors.setter
    # def emission_factors(self, value):
    #     try:
    #         assert Data.EmissionFactor.validate(value)
    #     except AssertionError:
    #         raise RuntimeError('{} failed validation: \n\n{}'.format('emission factors',
    #                                                                  value.head()))
    #     else:
    #         self._emission_factors = Data.EmissionFactor(df=value)
    #
    # @property
    # def fugitive_dust(self):
    #     return self._fugitive_dust
    #
    # @fugitive_dust.setter
    # def fugitive_dust(self, value):
    #     try:
    #         assert Data.FugitiveDust.validate(value)
    #     except AssertionError:
    #         raise RuntimeError('{} failed validation: \n\n{}'.format('emission factors',
    #                                                                  value.head()))
    #
    # @property
    # def fertilizer_distribution(self):
    #     return self._fertilizer_distribution
    #
    # @fertilizer_distribution.setter
    # def fertilizer_distribution(self, value):
    #     try:
    #         assert Data.FertilizerDistribution.validate(value)
    #     except AssertionError:
    #         raise RuntimeError('{} failed validation: \n\n{}'.format('emission factors',
    #                                                                  value.head()))
    #     else:
    #         self._fertilizer_distribution = Data.FertilizerDistribution(df=value)
    #
    # @property
    # def moisture_content(self):
    #     return self._moisture_content
    #
    # @moisture_content.setter
    # def moisture_content(self, value):
    #     try:
    #         assert Data.MoistureContent.validate(value)
    #     except AssertionError:
    #         raise RuntimeError('{} failed validation: \n\n{}'.format('emission factors',
    #                                                                  value.head()))
    #     else:
    #         self._moisture_content = Data.MoistureContent(df=value)

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
