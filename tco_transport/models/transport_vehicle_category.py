# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models


class HoranetTransportVehicleCategory(models.Model):
    """Category of a vehicle."""

    # region Private attributes
    _name = 'tco.transport.vehicle.category'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('name')
    def _check_name(self):
        """Check if the name is valid.

        :raise: odoo.exceptions.ValidationError if the field is empty
        """
        for rec in self:
            if len(rec.name.strip()) == 0:
                raise exceptions.ValidationError(_('Name cannot be empty'))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
