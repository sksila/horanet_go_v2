# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models

LINE_TYPE = [('outward', 'Outward'), ('return', 'Return')]


class HoranetTransportLine(models.Model):
    """Line is a path taken by a vehicle that goes through stops."""

    # region Private attributes
    _name = 'tco.transport.line'
    _sql_constraints = [
        (
            'unicity_on_name',
            'UNIQUE(name)',
            _('A line with this name already exists.')
        )
    ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)
    line_type = fields.Selection(
        string='Line type',
        selection=LINE_TYPE, required=True
    )

    line_stop_ids = fields.One2many(
        string='Line stops',
        comodel_name='tco.transport.stop',
        inverse_name='line_id'
    )
    begin_date = fields.Date(string='Begin date')
    end_date = fields.Date(string='End date')

    departure_time = fields.Float(
        string='Departure time',
        compute='_compute_departure_and_arrival_time'
    )
    arrival_time = fields.Float(
        string='Arrival time',
        compute='_compute_departure_and_arrival_time'
    )

    is_active_on_monday = fields.Boolean(string='Is active on monday')
    is_active_on_tuesday = fields.Boolean(string='Is active on tuesday')
    is_active_on_wednesday = fields.Boolean(string='Is active on wednesday')
    is_active_on_thursday = fields.Boolean(string='Is active on thursday')
    is_active_on_friday = fields.Boolean(string='Is active on friday')
    is_active_on_saturday = fields.Boolean(string='Is active on saturday')
    is_active_on_sunday = fields.Boolean(string='Is active on sunday')

    service_id = fields.Many2one(
        string='Service',
        comodel_name='tco.transport.service'
    )

    # endregion

    # region Fields method
    @api.multi
    @api.depends('line_stop_ids')
    def _compute_departure_and_arrival_time(self):
        """Compute the departure and arrival times of a line from its stops."""
        stop_model = self.env['tco.transport.stop']
        for rec in self:
            rec.departure_time = stop_model.get_stop_by_line_and_sequence(rec, 1).stop_time or False
            rec.arrival_time = stop_model.get_stop_by_line_and_sequence(rec, len(rec.line_stop_ids)).stop_time or None

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
