# -*- coding: utf-8 -*-
import logging
from odoo.addons.horanet_go.tools import migrations

__name__ = 'Remove is_up_to_date field'

logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    logger.info("Migration started")
    if not migrations.get_field_exists(cr, 'tpa_synchronization_status', 'is_up_to_date'):
        logger.info("Migration of query informations ended: no information to migrate.")
        return
    # Removing "is_up_to_date" field
    cr.execute("ALTER TABLE tpa_synchronization_status DROP COLUMN IF EXISTS is_up_to_date")
    logger.info("Migration ended")
