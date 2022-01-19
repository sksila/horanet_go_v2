# coding: utf-8

from odoo import models, fields


class InheritedResCompany(models.Model):
    # region Private attributes
    _inherit = 'res.company'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    ormc_id_post = fields.Char(
        string="IdPost",
        help="Value used to fill IdPost attribute in ORMC file",
        required=True,
    )
    ormc_cod_col = fields.Char(
        string="CodCol",
        help="Value used to fill CodCol attribute in ORMC file",
        required=True,
    )
    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
