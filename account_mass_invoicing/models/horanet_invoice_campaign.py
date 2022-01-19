# -*- coding: utf-8 -*-

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class HoranetInvoiceCampaign(models.Model):
    """
    This model represent invoicing campaigns.

    For example, you may want to invoice fixed part of a subscription on year 2018
    along with variable part on year 2017.
    You will then create one campaign with two campaign prestation periods.
    """

    # region Private attributes
    _name = 'horanet.invoice.campaign'
    _order = 'create_date desc'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name",
        required=True,
    )

    budget_code_id = fields.Many2one(string="Budget",
                                     comodel_name='horanet.budget.code',
                                     required=True)

    batch_ids = fields.One2many(
        string="Invoice batches",
        comodel_name='horanet.invoice.batch',
        inverse_name='campaign_id',
        readonly=True,
    )

    prestation_period_ids = fields.One2many(
        string="Prestation periods",
        comodel_name='horanet.campaign.prestation.period',
        inverse_name='campaign_id',
    )

    product_ids = fields.Many2many(
        string="Products",
        comodel_name='product.product',
    )
    # endregion

    # region Fields method
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
