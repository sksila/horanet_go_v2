# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Delete old value of containers_follows_producer in partner.setup.wizard and partner.wizard.close.contract.

    cause he's not used anymore.
    """
    logger.info('Migration started: delete containers_follows_producer field.')
    if not version:
        return

    # Drop "containers_follows_producer" field from "partner.setup.wizard", "partner.wizard.close.contract" model
    # cause he's not used anymore
    cr.execute("DELETE FROM ir_model_fields "
               "WHERE name = 'containers_follows_producer' AND model = 'partner.setup.wizard';")
    cr.execute("ALTER TABLE partner_setup_wizard DROP COLUMN IF EXISTS containers_follows_producer;")

    cr.execute("DELETE FROM ir_model_fields "
               "WHERE name = 'containers_follows_producer' AND model = 'partner.wizard.close.contract';")
    cr.execute("ALTER TABLE partner_wizard_close_contract DROP COLUMN IF EXISTS containers_follows_producer;")

    logger.info('Migration ended: delete containers_follows_producer config.')
