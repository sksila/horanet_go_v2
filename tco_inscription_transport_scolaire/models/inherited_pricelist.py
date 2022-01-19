# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class TCOPricelist(models.Model):
    """Surcharge du model product.pricelist pour y ajouter les inscriptions TCO."""

    # region Private attributes
    _inherit = 'product.pricelist'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    family_quotient_min = fields.Integer(string="family quotient min")
    family_quotient_max = fields.Integer(string="family quotient max")
    activate_tco = fields.Boolean(
        string="Activate tco inscription",
        default=False)
    no_family_quotient = fields.Boolean(
        string="No family quotient",
        default=False)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('activate_tco', 'no_family_quotient', 'family_quotient_min', 'family_quotient_max')
    def _check_unicity_tco_config(self):
        """Check unicity of TCO inscription configuration (mapping).

        :return: ValidationError if duplicate
        """
        for rec in self:
            if rec.activate_tco and (rec.family_quotient_min or rec.family_quotient_max or rec.no_family_quotient):
                domain = [('id', '!=', rec.id), ('activate_tco', '=', True)]
                if rec.no_family_quotient:
                    domain.extend([('no_family_quotient', '=', rec.no_family_quotient)])
                else:
                    if rec.family_quotient_min:
                        domain.extend(
                            [('family_quotient_max', '>', 0), ('family_quotient_max', '>=', rec.family_quotient_min)])
                    if rec.family_quotient_max:
                        domain.extend(
                            [('family_quotient_min', '>', 0), ('family_quotient_min', '<=', rec.family_quotient_max)])
                if self.search_count(domain):
                    raise exceptions.ValidationError(_("Family quotient cannot overlap with another price-list"))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
