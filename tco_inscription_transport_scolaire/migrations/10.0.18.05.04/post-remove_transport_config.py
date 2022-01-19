# -*- coding: utf-8 -*-

__name__ = 'Delete transport field config in horanet_go moved to model horanet transport config'

import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate old value of TCO transport config from horanet go/configs to transport/configs."""
    logger.info('Migration started: migrating transport config (background for cheque).')
    if not version:
        return

    # get id of "cheque_background_image" field from "horanet.transport.config" model
    cr.execute("""SELECT id FROM ir_model_fields
                  WHERE name='cheque_background_image' AND model = 'horanet.transport.config';""")
    ir_model_fields_obj = cr.fetchone()

    # Move value "cheque_background_image" from "collectivity.config.settings" model to "horanet.transport.config" model
    cr.execute("""UPDATE ir_property
                  SET fields_id = %s
                  WHERE name = 'cheque_background_image';""", ir_model_fields_obj)

    # Drop "cheque_background_image" field from "collectivity.config.settings" model cause he's not used anymore
    cr.execute("DELETE FROM ir_model_fields "
               "WHERE name = 'cheque_background_image' AND model = 'collectivity.config.settings';")
    cr.execute("ALTER TABLE collectivity_config_settings DROP COLUMN IF EXISTS cheque_background_image;")

    logger.info('Migration ended: migrating transport config (background for cheque).')
