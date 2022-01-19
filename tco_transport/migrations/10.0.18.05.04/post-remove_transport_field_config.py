# -*- coding: utf-8 -*-

__name__ = 'Delete transport field config in horanet_go moved to model horanet transport config'

import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):

    logger.info('Migration started: migrating transport config.')
    if not version:
        return

    cr.execute("DELETE FROM ir_model_fields "
               "WHERE model = 'collectivity.config.settings' AND name = 'terminal_lb7_directory_path';")
    cr.execute("ALTER TABLE collectivity_config_settings DROP COLUMN IF EXISTS terminal_lb7_directory_path;")

    cr.execute("DELETE FROM ir_model_fields "
               "WHERE model = 'collectivity.config.settings' AND name = 'lb7_time_offset';")
    cr.execute("ALTER TABLE collectivity_config_settings DROP COLUMN IF EXISTS lb7_time_offset;")

    logger.info('Migration ended: migrating transport config.')
