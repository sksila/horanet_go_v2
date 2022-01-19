# coding: utf-8

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Clear old external ID and it's linked record."""
    if not version:
        return
    _logger.info("Migration: Add on all subscription and template the application 'environment'")

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        subscription_to_update = env['horanet.subscription'].search([('application_type', '=', False)])
        subscription_to_update.write({'application_type': 'environment'})

        subscription_template_to_update = env['horanet.subscription.template'].search([])
        subscription_template_to_update.write({'application_type': 'environment'})

        _logger.info("Migration: done")
