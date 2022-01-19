# -*- coding: utf-8 -*-

import logging

from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HoranetInvoiceCampaign(models.Model):
    """Add constraint on product codes."""

    # region Private attributes
    _inherit = 'horanet.invoice.campaign'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('prestation_period_ids', 'product_ids')
    def _check_product_codes_consistency(self):
        """
        Check prestation periods.

        We can only have one product code for all invoices of a campaign.
        So we must ensure that all products of activities of all prestations involved in the campaign have the same
        product code.
        """
        for rec in self:
            product_codes = []
            if rec.prestation_period_ids:
                product_codes += rec.prestation_period_ids.mapped('prestation_ids.activity_ids.product_id.cod_prod_loc')
            if rec.product_ids:
                product_codes += rec.product_ids.mapped('cod_prod_loc')
            product_codes = set(product_codes)

            if len(product_codes) != 1:
                raise ValidationError(
                    _("There must be one and only one product code beyond all prestations involved.\n"
                        "Product codes found: {}.\n"
                        "Please, check activities products of prestations.").format(', '.join(list(product_codes))))
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
