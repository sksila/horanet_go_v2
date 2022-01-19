# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Post-install script to set the Payzen journal to the Payzen acquirer."""
    env = api.Environment(cr, SUPERUSER_ID, {})

    payzen = env.ref('payment_payzen.payment_acquirer_payzen')
    journal = env.ref('horanet_website_portal_sale.account_journal_payzen')
    if payzen:
        payzen.write({'journal_id': journal.id})
