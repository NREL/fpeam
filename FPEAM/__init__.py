from . import Data
# from . import Engine
from . import Figures
from .FPEAM import FPEAM
from . import IO
from . import Interfaces
from . import Modules
from . import utils

# Set default logging handler to avoid "No handler found" warnings.
import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

try:
    basestring
except NameError:
    basestring = str
