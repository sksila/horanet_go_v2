# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models


class HoranetTransportVehicleModel(models.Model):
    """Model of the brand of a vehicle."""

    # region Private attributes
    _name = 'tco.transport.vehicle.model'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)

    vehicle_category_id = fields.Many2one(
        string='Category',
        comodel_name='tco.transport.vehicle.category'
    )
    vehicle_brand_id = fields.Many2one(
        string='Brand',
        comodel_name='tco.transport.vehicle.brand'
    )

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
