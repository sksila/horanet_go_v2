# -*- coding: utf-8 -*-

from odoo import models, fields


class InheritedResCountry(models.Model):
    """Inherit res.country model to add 3 characters numeric field cod_pays for ORMC export."""

    # region Private attributes
    _inherit = 'res.country'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    ormc_cod_pays = fields.Char(string="CodPays", size=3)
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
