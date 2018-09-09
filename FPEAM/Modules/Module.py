import os
from FPEAM import (utils, IO)
from configobj import (ConfigObj, ConfigObjError)


LOGGER = utils.logger(name=__name__)


class Module(object):
    """Base class to describe modules"""

    def __init__(self, config):
        """

        :param config: [ConfigOjb] Module-specific config
        """

        self.__name__ = self.__module__.split('.')[-1].lower()

        self._config = None
        self._configspec = '%s.spec' % os.path.join(IO.CONFIG_FOLDER, self.__name__)

        self.config = config

        self.conversions = self._set_conversions()

        self.results = None
        self.status = 'new'
        self.graph = None

        return

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):

        try:
            value = ConfigObj(value)
        except TypeError:
            LOGGER.error('invalid configuration value passed for %s: %s' % (self.__name__, value))
            raise

        # merge incoming config with default values
        _config = ConfigObj('%s.ini' % os.path.join(IO.CONFIG_FOLDER, self.__name__))[self.__name__]
        _config.merge(value)
        LOGGER.debug('%s _config: %s' % (self.__name__, _config))

        # validate config
        _config = utils.validate_config(config=_config, spec=self._configspec)

        # @TODO: move errors/missing/extras parsing and logging to utils.validate_config function
        # @TODO: maybe move try/assert/raise in utils.validate_config as well? Then FPEAM.py can also use it
        _error = False

        for _k, _v in _config['errors'].items():
            LOGGER.error('%s config has invalid value: {%s: %s}' % (self.__name__, _k, _v))
            _error = True
        for _missing in _config['missing']:
            _error = True
            LOGGER.error('%s config is missing value: %s' % (self.__name__, _missing))
        for _k, _v in _config['extras'].items():
            LOGGER.warning('%s config has extra value: {%s: %s}' % (self.__name__, _k, _v))

        try:
            assert not _error
        except AssertionError:
            raise ConfigObjError('malformed config for %s; see output' % self.__name__)
        else:
            LOGGER.debug('validated %s config' % (self.__name__, ))
            self._config = _config['config']

    def _set_conversions(self):
        # @TODO: load from file so users can add additional conversions
        _conversions = dict()
        _conversions['tonne'] = dict()
        _conversions['tonne']['ton'] = 0.907018474   # 1 ton = 0.91 tonne  s

        _conversions['ton'] = dict()
        _conversions['ton']['pound'] = 1.0 / 2000.0  # 1 ton = 2000 lbs

        _conversions['mile'] = dict()
        _conversions['mile']['kilometer'] = 1.60934

        _conversions['kilometer'] = dict()
        _conversions['kilometer']['mile'] = 0.621371

        _conversions['gram'] = dict()
        _conversions['gram']['pound'] = 0.002204623

        return _conversions

    def run(self):
        """
        Execute module.

        :return: [bool] True on success
        """
        self.status = 'executed'
        self.graph = None
        self.results = None

    def save(self):
        """
        Save results.

        :return: [bool] True on success
        """

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
