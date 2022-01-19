# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class MassInvoicingAccountInvoice(models.Model):
    """Surcharge du model account.invoice pour y ajouter le lot de factures."""

    # region Private attributes
    _inherit = 'account.invoice'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    active = fields.Boolean(
        string="Active",
        default=True,
    )

    batch_id = fields.Many2one(
        string="Invoice batch",
        comodel_name='horanet.invoice.batch',
    )

    account_move_line_ids = fields.Many2many(comodel_name='account.move.line', compute='_compute_account_move_line_ids')

    subscription_id = fields.Many2one(
        string="Subscription",
        comodel_name='horanet.subscription',
        compute='_compute_subscription_id',
    )

    mandate_id = fields.Many2one(compute='_compute_mandate_id', store=True)
    payment_term_id = fields.Many2one(compute='_compute_payment_term_id', store=False)
    payment_mode_id = fields.Many2one(compute='_compute_payment_mode_id')

    # endregion

    # region Fields method
    @api.multi
    @api.depends('move_id')
    def _compute_account_move_line_ids(self):
        for rec in self:
            ids = []
            for aml in rec.move_id.line_ids:
                if aml.account_id.reconcile:
                    ids.extend(
                        [r.debit_move_id.id for r in aml.matched_debit_ids] if aml.credit > 0
                        else [r.credit_move_id.id for r in aml.matched_credit_ids])
                    ids.append(aml.id)

            rec.account_move_line_ids = ids

    @api.depends('origin')
    def _compute_subscription_id(self):
        for rec in self:
            origins = rec.origin and [r.strip() for r in rec.origin.split(',')] or []
            sale_orders = self.env['sale.order'].search([('name', 'in', origins)])
            subscription_lines = self.env['horanet.subscription.line'].search(
                [('sale_order_id', 'in', sale_orders.ids)])
            subscription = subscription_lines.mapped('subscription_id')
            if len(subscription) > 1:
                subscription = subscription[0]
                # raise ValidationError(_("All subsctiption lines of
                # a sale order must be of the same subscription : %d" % rec.id))

            rec.subscription_id = subscription

    @api.depends('subscription_id')
    def _compute_mandate_id(self):
        for rec in self:
            if rec.subscription_id.payment_mode.bank_account_required:
                rec.mandate_id = rec.subscription_id.banking_mandate or False
            else:
                rec.mandate_id = False

    @api.depends('subscription_id')
    def _compute_payment_term_id(self):
        for rec in self:
            rec.payment_term_id = rec.subscription_id and rec.subscription_id.get_active_line(
                search_date_utc=rec.date_invoice or fields.Datetime.now()
            ) and rec.subscription_id.payment_term_id or False

    @api.depends()
    def _compute_payment_mode_id(self):
        for rec in self:
            rec.payment_mode_id = False

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_open_timetable(self):
        return self.account_move_line_ids.open_reconcile_view()

    @api.multi
    def action_remove_from_batch(self):
        self.batch_id = False

    # endregion

    # region Model methods
    # endregion

    pass
