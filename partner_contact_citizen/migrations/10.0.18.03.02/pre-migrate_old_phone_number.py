# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate phone and mobile number."""
    logger.info('Migration started: phone and mobile number.')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

    partners = env['res.partner'].search([])

    for partner in partners:
        if partner.phone:
            try:
                partner.phone = partner.phone.replace(' ', '').replace('-', '').replace('.', '').replace('/', '')

            except Exception:
                logger.info("Phone number was not migrated for the partner %s." % (partner.id))

        if partner.mobile:
            try:
                partner.mobile = partner.mobile.replace(' ', '').replace('-', '').replace('.', '').replace('/', '')

            except Exception:
                logger.info("Mobile number was not migrated for the partner %s." % (partner.id))

    logger.info('Migration ended: phone and mobile number.')
