"""Manage execution of modules."""
import Modules
import utils
from IO import CONFIG_FOLDER
import os


LOGGER = utils.logger(name=__name__)


class Engine(object):

    """Execute modules."""

    # @TODO: can't these be discovered via the Modules module?
    MODULES = {'chemical': Modules.Chemical,
               'fugitive_dust': Modules.FugitiveDust,
               'MOVES': Modules.MOVES,
               'NONROAD': Modules.NONROAD}

    def __init__(self, budget, production, config, fertilizers=None, emission_factors=None):
        """
        Create a new Engine.

        :param budget: [Budget]
        :param production: [Production]
        :param config: [ConfigObj]
        :param fertilizers [Fertilizers]
        :param emission_factors [EmissionFactors]
        """

        self.config = config

        self.budget = budget
        self.production = production
        self.fertilizers = fertilizers
        self.emission_factors = emission_factors

        return

    def run(self, module):
        """
        Execute <module>.

        :param module: [FPEAM.Module] with run() and save() method
        :return: [bool] True on success
        """

        try:
            LOGGER.info('running module: {}'.format(module))
            with Engine.MODULES[module](config=self.config[module],
                                        configspec=os.path.join(CONFIG_FOLDER, '%s.spec' % module),
                                        budget=self.budget,
                                        production=self.production,
                                        fertilizers=self.fertilizers,
                                        emission_factors=self.emission_factors) as _module:
                _result = _module.run()
        except KeyError:
            if module not in Engine.MODULES.keys():
                LOGGER.warning('invalid module name: {}.'
                               ' Must be one of: {}'.format(module,
                                                            Engine.MODULES.keys()))
        else:
            return _result

    def run_all(self, modules):
        """
        Execute all <modules>.

        :param modules: [list] modules with run() and save() methods and graph property
        :return: [dict] {module_name: {status: int, results: DataFrame, errors: list}}
        """

        _results = {}

        for _module in modules:
            _result = self.run(module=_module)
            LOGGER.info('{}: {}'.format(_module, _result['status']))
            _results[_module] = _result

        return _results

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
        return
