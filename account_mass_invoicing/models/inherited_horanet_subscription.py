# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging
# 2 :  imports of openerp
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MassInvoicingHoranetSubscription(models.Model):
    """Surcharge du model horanet.subscription pour y ajouter le mode de paiement."""

    # region Private attributes
    _inherit = 'horanet.subscription'
    # endregion

    # region Default methods
    @api.model
    def _get_default_payment_mode(self):
        payment_method = self.env.ref('account_mass_invoicing.payment_method_not_withdrawn', False)
        return payment_method and payment_method.id
    # endregion

    # region Fields declaration
    payment_mode = fields.Many2one(
        string="Payment mode",
        comodel_name='account.payment.method',
        default=_get_default_payment_mode,
    )

    banking_mandate = fields.Many2one(
        string="Banking mandate",
        comodel_name='account.banking.mandate',
        domain="[('partner_id', '=', client_id)]"
    )

    bank_account_id = fields.Many2one(
        string="Bank account",
        comodel_name='res.partner.bank',
        domain="[('partner_id', '=', client_id)]",
    )
    required_mandate = fields.Boolean(
        related='payment_mode.bank_account_required',
        readonly=True,
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.onchange('banking_mandate')
    def _on_change_banking_mandate(self):
        if self.banking_mandate:
            self.bank_account_id = self.banking_mandate.partner_bank_id

    @api.constrains('banking_mandate', 'bank_account_id')
    def check_banking_data(self):
        """
        Check the consistency of banking data.

        :return: nothing
        :raise: Validation error if banking mandate's account doesn't match bank account
        """
        for rec in self:
            # KO si la date de fin est renseignée mais inférieure à la date de début
            if rec.banking_mandate and rec.banking_mandate.partner_bank_id != rec.bank_account_id:
                raise ValidationError(_(u"Banking mandate's account doesn't match bank account."))
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
