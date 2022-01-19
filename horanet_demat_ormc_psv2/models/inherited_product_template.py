# coding: utf-8

from odoo import fields, models, api, exceptions, _


class InheritedProductTemplate(models.Model):
    # region Private attributes
    _inherit = 'product.template'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    cod_prod_loc = fields.Char(
        string='CodProdLoc',
        help='Value used to fill CodProdLoc attribute in ORMC file',
        required=True
    )

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    @api.constrains('cod_prod_loc')
    def _check_cod_prod_loc(self):
        for rec in self:
            if len(rec.cod_prod_loc) > 4:
                raise exceptions.UserError(_(
                    "The length of cod_prod_loc must be maximum four characters."
                ))
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
