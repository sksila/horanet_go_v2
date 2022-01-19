# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Delete old value of containers_follows_producer config from horanet.environment.config.

    Because we move this config in the equipment model.
    """
    logger.info('Migration started: delete containers_follows_producer config.')
    if not version:
        return

    # Drop "containers_follows_producer" field from "horanet.environment.config",
    # "partner.setup.wizard", "partner.wizard.close.contract" model cause he's not used anymore
    cr.execute("DELETE FROM ir_model_fields "
               "WHERE name = 'containers_follows_producer' AND model = 'horanet.environment.config';")
    cr.execute("ALTER TABLE horanet_environment_config DROP COLUMN IF EXISTS containers_follows_producer;")

    cr.execute("DELETE FROM ir_config_parameter "
               "WHERE key = 'environment_production_point.containers_follows_producer';")

    logger.info('Migration ended: delete containers_follows_producer config.')
