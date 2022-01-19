# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields

_logger = logging.getLogger(__name__)


class TCOSaleOrder(models.Model):
    """Surcharge du model sale.order pour y ajouter les inscriptions TCO."""

    # region Private attributes
    _inherit = 'sale.order'

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
    def _prepare_invoice(self):
        u"""Surcharge de la méthode 'faussement' privée de génération de facture.

        afin de propager la date dedécalage (optionnelle) de début d'échéancier du sale.order vers l'account.invoice
        """
        invoice_vals = super(TCOSaleOrder, self)._prepare_invoice()
        if self.date_payment_term_start:
            invoice_vals['date_payment_term_start'] = self.date_payment_term_start
        return invoice_vals

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
