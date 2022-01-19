# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Re-confirm subscriptions.

    As we transformed the state field into a computed field, and because for
    some reason, subscriptions don't have starting_date, let's re-confirm them.
    """
    if not version:
        return

    _logger.info('Start migration: re-confirm subscriptions')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        subscriptions = env['horanet.subscription'].search([('state', '=', 'draft')])
        subscriptions.action_confirm_subscription()
        _logger.info('End migration: %s subscriptions re-confirmed' % len(subscriptions))
