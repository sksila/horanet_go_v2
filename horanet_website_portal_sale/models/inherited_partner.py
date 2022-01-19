# coding: utf-8

from odoo import fields
from odoo.osv import osv


class ResPartner(osv.Model):
    _inherit = 'res.partner'

    property_account_supplier_advance = fields.Many2one(
        comodel_name='account.account',
        string="Account Supplier Advance",
        domain="[('user_type_id.type','=','payable')]",
        help="This account will be used for advance payment of suppliers")
    property_account_customer_advance = fields.Many2one(
        comodel_name='account.account',
        string="Account Customer Advance",
        domain="[('user_type_id.type','=','receivable')]",
        help="This account will be used for advance payment of customer")

    bank_account_count_button = fields.Integer(
        related='bank_account_count'
    )
