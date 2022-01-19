# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models

_logger = logging.getLogger(__name__)


class InheritAccountMoveLine(models.Model):
    """Inherit account move line model to add ORMC debit amount compute fonction."""

    # region Private attributes
    _inherit = 'account.move.line'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    def get_ormc_debit(self):

        invoice_move_lines = self.invoice_id.account_move_line_ids

        total_debit = sum(invoice_move_lines.mapped('debit'))
        total_credit = sum(invoice_move_lines.mapped('credit')) + sum(invoice_move_lines.filtered(
            lambda aml: aml.debit > 0.0 and aml.date_maturity < self.date_maturity).mapped('debit'))
        balance = total_debit - total_credit

        if 0.0 < self.debit <= balance:
            return self.debit
        elif 0.0 < balance < self.debit:
            return balance
        return 0.0
    # endregion
