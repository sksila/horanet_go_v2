# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HoranetCampaignPrestationPeriod(models.Model):
    """
    This model tells which prestation we will invoice for a campaign and on which period.

    For example, you may want to invoice fixed part of a subscription on year 2018
    along with variable part on year 2017.
    You will then create one campaign with two campaign prestation periods.
    """

    # region Private attributes
    _name = 'horanet.campaign.prestation.period'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    campaign_id = fields.Many2one(
        string="Campaign",
        comodel_name='horanet.invoice.campaign',
    )
    prestation_ids = fields.Many2many(
        string="Prestations",
        comodel_name='horanet.prestation',
        required=True,
    )
    start_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )
    end_date = fields.Date(
        required=True,
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('start_date', 'end_date')
    def _check_date_consistency(self):
        for rec in self:
            if rec.end_date < rec.start_date:
                raise ValidationError(_("End date should be posterior or equal to start date."))

    @api.constrains('campaign_id', 'prestation_id', 'start_date', 'end_date')
    def _check_unicity(self):
        u"""Vérifie l'unicité de la facturation de cette prestation pour cette campagne sur ces dates."""
        for rec in self:
            periods = self.search([
                ('campaign_id', '=', rec.campaign_id.id),
                ('prestation_ids', '=', rec.prestation_ids.ids),
                ('id', '!=', rec.id)
            ])

            for period in periods:
                if (rec.start_date <= period.start_date <= rec.end_date or
                   period.start_date <= rec.start_date <= period.end_date):
                    raise ValidationError(
                        _("This prestation is already on this campaign for the provided dates"))
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
