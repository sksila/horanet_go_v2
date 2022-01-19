# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models
from odoo.addons import decimal_precision as dp


class HoranetTransportStation(models.Model):
    """A station represents the physical location of a stop."""

    # region Private attributes
    _name = 'tco.transport.station'
    _sql_constraints = [
        (
            'unicity_on_station_number',
            'UNIQUE(station_number)',
            _('A station with this number already exists.')
        )
    ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)
    station_number = fields.Char(string='Station Number', required=True)

    longitude = fields.Float(string='Longitude', digits=dp.get_precision('Transport localisation decimal'))
    latitude = fields.Float(string='Latitude', digits=dp.get_precision('Transport localisation decimal'))
    type_id = fields.Many2one(
        string='Type',
        comodel_name='tco.transport.station.type'
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

    @api.constrains('name')
    def _check_serial_number(self):
        """Check if the station_number is valid.

        :raise: odoo.exceptions.ValidationError if the field is empty
        """
        for rec in self:
            if len(rec.station_number.strip()) == 0:
                raise exceptions.ValidationError(_('Station number cannot be empty'))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
