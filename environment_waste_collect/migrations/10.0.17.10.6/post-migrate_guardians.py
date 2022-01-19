# coding: utf-8

import logging
from odoo import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate guardian partners.

    As we removed is_environment_guardian field in favor of guardian tag,
    we need to migrate previous partners tagged as guardian.
    """
    logger.info('Migration started: migrating guardian partners.')
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        if 'is_environment_guardian' in env['res.partner'].fields_get_keys():
            partners = env['res.partner'].search([('is_environment_guardian', '=', True)])
            if not partners:
                logger.info("Migration ended: no partner to migrate.")
            else:
                partners.write({
                    'category_id': [(4, env.ref('environment_waste_collect.partner_category_guardian').id)]
                })
            logger.info('Migration ended: %s partner(s) migrated.' % len(partners))
        else:
            logger.info("Migration ended: field 'is_environment_guardian' never existed.")
