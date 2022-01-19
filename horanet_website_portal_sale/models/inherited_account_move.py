# -*- coding: utf-8 -*-
import logging

from odoo import models
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    """Class to override auto_reconcile_lines to use a custom_get_pair_to_reconcile.

    used to have move lines order by due date and not date.
    """

    _inherit = "account.move.line"

    def _get_pair_to_reconcile(self):
        u"""Override the original fonction from Account.

        We get the pair of move lines to reconcile based on their credit or debit. Pairs are sorted by date_maturity
        """
        # field is either 'amount_residual' or 'amount_residual_currency'
        # (if the reconciled account has a secondary currency set)
        field = self[0].account_id.currency_id and 'amount_residual_currency' or 'amount_residual'
        rounding = self[0].company_id.currency_id.rounding
        if self[0].currency_id and all([x.amount_currency and x.currency_id == self[0].currency_id for x in self]):
            # or if all lines share the same currency
            field = 'amount_residual_currency'
            rounding = self[0].currency_id.rounding
        if self._context.get('skip_full_reconcile_check') == 'amount_currency_excluded':
            field = 'amount_residual'
        elif self._context.get('skip_full_reconcile_check') == 'amount_currency_only':
            field = 'amount_residual_currency'
        # target the pair of move in self that are the oldest
        # THIS is where we change a.date to a.date_maturity
        sorted_moves = sorted(self, key=lambda a: a.date_maturity)
        debit = credit = False
        for aml in sorted_moves:
            if credit and debit:
                break
            if float_compare(aml[field], 0, precision_rounding=rounding) == 1 and not debit:
                debit = aml
            elif float_compare(aml[field], 0, precision_rounding=rounding) == -1 and not credit:
                credit = aml
        return debit, credit
