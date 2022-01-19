# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HoranetInvoiceBatchType(models.Model):
    """This model represents type of invoicing batch.

    The records of this model are intended to be created once at the beginning.
    """

    # region Private attributes
    _inherit = 'application.type'
    _name = 'horanet.invoice.batch.type'
    _sql_constraints = [('unicity_on_application_and_category_and_mode',
                         'UNIQUE(application_type,partner_category_id,payment_mode_id)',
                         _('The association mode / category must be unique'))]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name",
        compute='_compute_name',
    )

    partner_category_id = fields.Many2one(
        string="Partner category",
        comodel_name='subscription.category.partner',
        required=True,
    )
    payment_mode_id = fields.Many2one(
        string="Payment mode",
        comodel_name='account.payment.method',
    )

    # endregion

    # region Fields method
    @api.depends('application_type', 'partner_category_id', 'payment_mode_id')
    def _compute_name(self):
        for rec in self:
            parts = [
                p for p in [dict(rec._fields['application_type'].selection).get(rec.application_type),
                            rec.partner_category_id.name, rec.payment_mode_id.name] if p
            ]
            rec.name = ' - '.join(parts)

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
