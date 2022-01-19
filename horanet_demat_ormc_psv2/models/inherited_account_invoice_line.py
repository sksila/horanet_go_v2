# -*- coding: utf-8 -*-
from odoo import models, fields, api


class InheritedAccountInvoiceLine(models.Model):
    # region Private attributes
    _inherit = 'account.invoice.line'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    price_tva_value = fields.Monetary(
        string='Price TVA',
        currency_field='company_currency_id',
        store=True,
        readonly=True,
        compute='_compute_price_tva',
        help="Total amount in the currency of the company, negative for credit notes.")

    # endregion

    # region Fields method
    @api.depends('price_unit', 'price_subtotal')
    def _compute_price_tva(self):
        for rec in self:
            rec.price_tva_value = rec.price_subtotal - rec.price_subtotal

    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    def get_code_res_deb(self):
        return self.invoice_id.get_code_res_deb()
    # endregion
