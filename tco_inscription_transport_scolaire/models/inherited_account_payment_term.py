# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api, exceptions, _
from ..config import config

_logger = logging.getLogger(__name__)


class AccountPaymentTerm(models.Model):
    """Surcharge du model account.payment.term pour y ajouter les inscriptions TCO."""

    # region Private attributes
    _inherit = 'account.payment.term'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    activate_tco = fields.Boolean(
        string="Activate tco inscription",
        default=False)
    tco_inscription_invoice_period = fields.Selection(
        string="tco invoice period",
        selection=config.INSCRIPTION_INVOICE_PERIOD,
        default=None)
    tco_period_id = fields.Many2one(
        string="tco inscription period",
        comodel_name='tco.inscription.period')

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('activate_tco', 'tco_inscription_invoice_period', 'tco_period_id')
    def _check_unicity_tco_config(self):
        """Check unicity of TCO inscription configuration (mapping).

        :return: ValidationError if duplicate
        """
        for rec in self:
            if rec.activate_tco:
                duplicate = self.search([('id', '!=', rec.id),
                                         ('activate_tco', '=', True),
                                         ('tco_period_id', '=', rec.tco_period_id.id),
                                         ('tco_inscription_invoice_period', '=', rec.tco_inscription_invoice_period)],
                                        limit=1)
                if duplicate:
                    raise exceptions.ValidationError(
                        _("Payment term {name} has the same tco inscription configuration").format(
                            name=duplicate.name))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
