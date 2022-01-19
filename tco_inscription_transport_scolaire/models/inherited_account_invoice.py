# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class TCOAccountInvoice(models.Model):
    """Surcharge du model account.invoice pour y ajouter les inscriptions TCO."""

    # region Private attributes
    _inherit = 'account.invoice'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    date_payment_term_start = fields.Date(string="Delayed payment term")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.onchange('payment_term_id', 'date_invoice')
    def _onchange_payment_term_date_invoice(self):
        u"""Surcharge de la méthode appelé lors du changement de date de facturation.

        qui elle même appellela méthode de calcul du payment.term si il existe (payment_term.compute()),
        pour forcer la date de début de création d'échéancier
        """
        if self.payment_term_id and self.date_payment_term_start:
            self.date_invoice = self.date_payment_term_start
        return super(TCOAccountInvoice, self)._onchange_payment_term_date_invoice()

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
