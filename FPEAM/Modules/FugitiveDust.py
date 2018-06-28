from Module import Module

from FPEAM import (Data, utils)

LOGGER = utils.logger(name=__name__)


class FugitiveDust(Module):
    """Base class to manage execution of Transporation emissions"""

    def __init__(self, config, **kvals):

        # init parent
        super(FugitiveDust, self).__init__(config=config)

    def _pre_process(self):
        # merges budget and product data
        return

    def _post_process(self):
        return

    # def __enter__(self):
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     # process exceptions
    #     if exc_type is not None:
    #         LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
    #         return False
    #     else:
    #         return self


class OnFarmFugitiveDust(FugitiveDust):
    """Class to manage execution of on-farm fugitive dust emissions"""

    def __init__(self, config):
        # init parent
        super(FugitiveDust, self).__init__(config=config)

    def proceess(self):
        # calculate emissions
        return

    # def __enter__(self):
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     # process exceptions
    #     if exc_type is not None:
    #         LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
    #         return False
    #     else:
    #         return self


class OnRoadFugitiveDust(FugitiveDust):
    """Class to manage execution of on-road fugitive dust emissions"""

    def __init__(self, config):
        # init parent
        super(FugitiveDust, self).__init__(config=config)

    def process(self):
        # calculate
        return

    # def __enter__(self):
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     # process exceptions
    #     if exc_type is not None:
    #         LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
    #         return False
    #     else:
    #         return self
