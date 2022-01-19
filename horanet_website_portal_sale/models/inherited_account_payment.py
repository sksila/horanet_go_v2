# -*- coding: utf-8 -*-
from odoo import fields
from odoo.osv import osv


class AccountPayment(osv.Model):
    """Add an advance account to the payment model."""

    _inherit = 'account.payment'

    advance_account_id = fields.Many2one(
        string="Advance Account",
        comodel_name='account.account',
        required=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
