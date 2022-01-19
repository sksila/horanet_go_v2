# -*- coding: utf-8 -*-

import logging

from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InheritedCampaignPrestationPeriod(models.Model):
    """Add constraint on product codes."""

    # region Private attributes
    _inherit = 'horanet.campaign.prestation.period'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('prestation_ids')
    def _check_prestations_consistency(self):
        """
        Check prestations.

        We can only have one product code for all invoices of a campaign.
        So we must ensure that all products of activities of all prestations involved in the campaign have the same
        product code.
        """
        for rec in self:
            product_codes = set(rec.prestation_ids.mapped('activity_ids.product_id.cod_prod_loc'))
            if len(product_codes) != 1:
                raise ValidationError(
                    _("""There must be one and only one product code beyond all prestations involved.\n
                    Product codes found: {}.\n
                    Please, check activities products of prestations.""").format(', '.join(list(product_codes))))
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
