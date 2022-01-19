# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, api

_logger = logging.getLogger(__name__)


class MassInvoicingAccountPaymentMethod(models.Model):
    """Surcharge du model account.payment.method pour changer le nom."""

    # region Private attributes
    _inherit = 'account.payment.method'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    @api.depends('code', 'name', 'payment_type')
    def name_get(self):
        result = []
        for method in self:
            result.append((
                method.id, method.name
            ))
        return result
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
