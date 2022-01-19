# coding: utf-8

import logging

from psycopg2 import ProgrammingError

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Modify parameter noupdate of guardian partner category.

    As we changed the domain of guardian partner category, we need to update it.
    It was created with noupdate=1. So we update ir_model_data to set noupdate to 0.
    """
    logger.info('Migration started: updating noupdate parameter of environment_category_guardian data.')
    if not version:
        return

    try:
        cr.execute("UPDATE ir_model_data SET noupdate = false WHERE module = 'environment_waste_collect' and "
                   "name = 'environment_category_guardian'")
    except ProgrammingError:
        logger.info('Migration ended: no record to update.')
        return

    logger.info('Migration ended: environment_category_guardian data updated.')
