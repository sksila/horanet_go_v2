# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Add on operation the partner linked to an equipment, the partner is now a store field."""
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        operation_to_update = env['horanet.operation'].search([
            ('maintenance_equipment_id', '!=', False),
            ('partner_id', '=', False)
        ])
        _logger.info("Migration started: updating operation linked to an equipment."
                     " Number to update : {op_number}".format(op_number=str(len(operation_to_update))))

        current_number = 0
        for operation in operation_to_update:
            current_number += 1
            if not current_number % 100:
                _logger.info("Updating operation #{current} / {total}".format(
                    current=str(current_number),
                    total=str(len(operation_to_update))))

            operation_move = operation.maintenance_equipment_id.get_equipment_move(search_date_utc=operation.time)
            operation.partner_id = operation_move.partner_id

        _logger.info('End migration')
