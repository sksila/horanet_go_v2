# -*- coding: utf-8 -*-

from odoo import models, fields, _


class HoranetVehicleType(models.Model):
    """This class represent a model of vehicle type."""

    # region Private attributes
    _name = 'partner.contact.identification.vehicle.type'
    _sql_constraints = [('unicity_on_code', 'UNIQUE(code)', _("The code must be unique !"))]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name",
        required=True,
    )

    code = fields.Char(
        string="Code",
        required=True,
    )

    country_id = fields.Many2one(
        string="Country",
        comodel_name='res.country',
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
