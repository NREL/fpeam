from Module import Module

from FPEAM import (Data, utils)

LOGGER = utils.logger(name=__name__)


class FugitiveDust(Module):
    """Base class to manage execution of on-farm fugitive dust calculations"""

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
