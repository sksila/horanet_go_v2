# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api, exceptions, _
from ..config import config

_logger = logging.getLogger(__name__)


class TCOProduct(models.Model):
    """Surcharge du model product.product pour y ajouter les inscriptions TCO."""

    # region Private attributes
    _inherit = 'product.product'
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
    tco_inscription_is_derogation = fields.Boolean(string="tco incription derogation")
    tco_inscription_is_student = fields.Boolean(string="tco inscription student")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('activate_tco', 'tco_inscription_invoice_period', 'tco_inscription_is_student',
                    'tco_inscription_is_derogation')
    def _check_unicity_tco_config(self):
        """Check unicity of TCO inscription configuration (mapping).

        :return: ValidationError if duplicate
        """
        for rec in self:
            if rec.activate_tco:
                duplicate = self.search([('id', '!=', rec.id),
                                         ('activate_tco', '=', True),
                                         ('product_tmpl_id', '=', rec.product_tmpl_id.id),
                                         ('tco_inscription_invoice_period', '=', rec.tco_inscription_invoice_period),
                                         ('tco_inscription_is_derogation', '=', rec.tco_inscription_is_derogation),
                                         ('tco_inscription_is_student', '=', rec.tco_inscription_is_student)], limit=1)
                if duplicate:
                    raise exceptions.ValidationError(
                        _("Product {name} has the same tco inscription configuration").format(
                            name=duplicate.display_name))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
