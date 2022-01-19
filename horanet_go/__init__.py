from . import models
from . import tools
from . import controller
from . import version

import logging
from .hooks import pre_init_hook
from .hooks import post_init_hook

__version__ = version.__version__

_logger = logging.getLogger('odoo.addons.horanet_go')
_logger.info("Running Horanet GO version " + str(__version__))
