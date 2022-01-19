# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """The field time is added to improve the field create_date which was used as time."""
    if not version:
        return

    _logger.info('Start cron migration:')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # modification du nom de la méthode appelé par le cron (normalement inutile car noupdate = False)
        cron_operation = env.ref('horanet_subscription.scheduler_engine_operations', raise_if_not_found=False)
        if cron_operation:
            cron_operation.function = '_cron_compute_operation'

        # Pour forcer la modification du noupdate du fichier de data xml, modification de l'external_id
        external_id = env['ir.model.data'].search([
            ('module', '=', 'horanet_subscription'),
            ('name', '=', 'scheduler_engine_operations')])
        if external_id:
            external_id.noupdate = True

        _logger.info('End cron migration')
