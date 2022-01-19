# -*- coding: utf-8 -*-

from odoo.addons.base_iban.models.res_partner_bank import validate_iban

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountingDataSetUpPartner(models.TransientModel):
    u"""Wizard assistant de création de partner environnement."""

    # region Private attributes
    _inherit = 'partner.setup.wizard'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # Accounting data

    bank_account = fields.Many2one(
        string="Bank account",
        comodel_name='res.partner.bank',
        domain="[('partner_id', '=', partner_id)]")

    iban = fields.Char(string="IBAN", help="International Bank Account Number ")
    bic = fields.Char(string="BIC code", help="Bank Identifier Code, also know as SWIFT code")
    bank_name = fields.Char(string="Bank name")
    payment_mode = fields.Many2one(string="Payment mode", related='subscription_id.payment_mode')
    payment_term_id = fields.Many2one(string="Payment term", related='subscription_id.payment_term_id')

    banking_mandate = fields.Many2one(
        string="Banking Mandate",
        related='subscription_id.banking_mandate',
        domain="[('partner_id', '=', partner_id)]",
        readonly=True)

    iban_mandate = fields.Many2one(
        string="Iban of the mandate",
        related='banking_mandate.partner_bank_id',
        readonly=True)

    mandate_signature_date = fields.Date(string="Mandate signature date", default=fields.Date.context_today)

    bank_account_required = fields.Boolean(string="Iban required", related='payment_mode.bank_account_required')
    has_mandate = fields.Boolean(string="Has mandate", compute='_compute_has_mandate')

    create_or_select_mandate = fields.Selection(
        selection=[
            ('select', 'Select Mandate'),
            ('new', 'New Mandate'),
        ],
        default='select')

    create_or_select_iban = fields.Selection(
        selection=[
            ('select', 'Select IBAN'),
            ('new', 'New IBAN'),
        ],
        default='select')

    # endregion

    # region Fields method
    @api.depends('banking_mandate')
    def _compute_has_mandate(self):
        if self.banking_mandate:
            self.has_mandate = True

    # endregion

    # region Constrains and Onchange
    @api.onchange('has_mandate', 'create_or_select_mandate')
    def _onchange_create_or_select_mandate(self):
        if self.has_mandate is False:
            self.create_or_select_mandate = 'new'

    @api.onchange('bank_account', 'create_or_select_iban')
    def _onchange_create_or_select_iban(self):
        if self.env['res.partner.bank'].search_count([('partner_id', '=', self.partner_id.id)]) == 0:
            self.create_or_select_iban = 'new'

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_create_mandate(self):
        self.ensure_one()
        new_iban_create = self.env['res.partner.bank']

        if self.create_or_select_iban == 'select':
            self.banking_mandate = self.env['account.banking.mandate'].create(
                {'partner_bank_id': self.bank_account.id,
                 'type': 'recurrent',
                 'recurrent_sequence_type': 'recurring',
                 'signature_date': self.mandate_signature_date,
                 })
        else:
            validate_iban(self.iban)
            self.iban = self.iban.upper()
            new_bank_id = None
            new_bank_name = None
            if self.bank_name and self.bic:
                if len(self.bic) == 8 or len(self.bic) == 11:
                    # we don't create the bank if she already exists
                    bank_existing = self.env['res.bank'].search([('bic', '=', self.bic)])
                    if bank_existing:
                        new_bank = bank_existing
                    else:
                        new_bank = self.env['res.bank'].create({'name': self.bank_name,
                                                                'bic': self.bic})
                    new_bank_id = new_bank.id
                    new_bank_name = new_bank.name

                else:
                    raise ValidationError(_("The BIC code must have 8 or 11 characters"))
            elif self.bank_name:
                new_bank = self.env['res.bank'].create({'name': self.bank_name})
                new_bank_id = new_bank.id
                new_bank_name = new_bank.name

            new_iban_create = self.env['res.partner.bank'].create({'acc_number': self.iban,
                                                                   'partner_id': self.partner_id.id,
                                                                   'bank_id': new_bank_id,
                                                                   'bank_name': new_bank_name}).id

            self.banking_mandate = self.env['account.banking.mandate'].create(
                {'partner_bank_id': new_iban_create,
                 'type': 'recurrent',
                 'recurrent_sequence_type': 'recurring',
                 'signature_date': self.mandate_signature_date,
                 })

        # update the subscription banking mandate
        self.subscription_id.write({
            'banking_mandate': self.banking_mandate.id,
            'bank_account_id': new_iban_create if new_iban_create else self.bank_account.id,
        })

        # put default state of fields for new Mandate
        self.create_or_select_mandate = 'select'
        self.create_or_select_iban = 'select'
        self.mandate_signature_date = None
        self.iban = None
        self.bank_name = None
        self.bic = None

        return self._self_refresh_wizard()

    # region Model methods
    # endregion

    pass
