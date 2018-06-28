from Module import Module

from FPEAM import utils

LOGGER = utils.logger(name=__name__)


class NONROAD(Module):
    def __init__(self, config, **kvals):
        # init parent
        super(NONROAD, self).__init__(config=config)

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
