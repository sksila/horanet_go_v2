# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """The field time is added to improve the field create_date which was used as time."""
    if not version:
        return

    _logger.info('Start assignation move migration:')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        assignation_model = env['partner.contact.identification.assignation']
        assignation_to_update = assignation_model.search([('reference_id', '=like', 'partner.move,%')])

        if assignation_model._fields.get('move_id', False):
            env.add_todo(assignation_model._fields['move_id'], assignation_to_update)
        if assignation_model._fields.get('partner_id', False):
            env.add_todo(assignation_model._fields['partner_id'], assignation_to_update)
        if assignation_model._fields.get('package_id', False):
            env.add_todo(assignation_model._fields['package_id'], assignation_to_update)

        assignation_model.recompute()

    _logger.info('End assignation move migration')
