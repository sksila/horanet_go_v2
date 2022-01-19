# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class HoranetTransportStop(models.Model):
    """Stop represents where / when vehicles will stop on a line."""

    # region Private attributes
    _name = 'tco.transport.stop'
    _rec_name = 'station_id'
    _sql_constraints = [
        (
            'unicity_on_stop_distance',
            'UNIQUE(line_id,stop_distance)',
            _('TODO')
        )
    ]
    _order = 'stop_distance'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    line_id = fields.Many2one(
        string='Line',
        comodel_name='tco.transport.line',
        required=True
    )
    station_id = fields.Many2one(
        string='Station',
        comodel_name='tco.transport.station',
        required=True
    )
    stop_distance = fields.Integer(string='Stop distance (in meters)', required=True, index=True)
    stop_time = fields.Float(string='Stop time', required=True)

    sequence = fields.Integer(
        string='Sequence', compute='_compute_sequence', store=False
    )
    distance_from_previous_station = fields.Integer(
        string='Distance from previous station (in meters)',
        compute='_compute_distance_from_previous_station',
        store=False
    )
    previous_stops_ids = fields.Many2many(
        string="Previous stops",
        comodel_name='tco.transport.stop',
        compute='_compute_previous_stops_ids',
        store=False)
    next_stops_ids = fields.Many2many(
        string="Next stops",
        comodel_name='tco.transport.stop',
        compute='_compute_next_stops_ids',
        store=False)

    # endregion

    # region Fields method
    @api.depends('previous_stops_ids')
    def _compute_sequence(self):
        """Compute the position of a stop against another ones on the same line."""
        for rec in self:
            rec.sequence = len(rec.previous_stops_ids) + 1

    @api.depends('stop_distance', 'line_id')
    def _compute_previous_stops_ids(self):
        """Compute the position of a stop against another ones on the same line: previous stops."""
        for rec in self:
            rec.previous_stops_ids = self.search(
                [('line_id', '=', rec.line_id.id), ('stop_distance', '<', rec.stop_distance)],
                order='stop_distance')

    @api.depends('stop_distance', 'line_id')
    def _compute_next_stops_ids(self):
        """Compute the position of a stop against another ones on the same line: next stops."""
        for rec in self:
            rec.next_stops_ids = self.search(
                [('line_id', '=', rec.line_id.id), ('stop_distance', '>', rec.stop_distance)],
                order='stop_distance')

    @api.depends('stop_distance')
    def _compute_distance_from_previous_station(self):
        """Compute distance between each stops on a line."""
        for rec in self:
            previous_rec = self.search(
                [('line_id', '=', rec.line_id.id),
                 ('stop_distance', '<', rec.stop_distance)],
                limit=1, order='stop_distance desc'
            )
            if previous_rec:
                rec.distance_from_previous_station = rec.stop_distance - previous_rec.stop_distance
            else:
                rec.distance_from_previous_station = 0

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def get_stop_by_line_and_sequence(self, line, sequence):
        """Return stop ordered by stop_distance.

        :param line: tco.transport.line record to filter on
        :param sequence: sequence of the stop to filter on
        """
        # TODO: Check if sequence is really used as we only retrieve one row
        # with limit=1, not sure if the offset is necessary
        return self.search(
            [('line_id', '=', line.id)],
            order='stop_distance asc',
            offset=sequence and sequence - 1 or 0,
            limit=1
        )

    # endregion

    pass
