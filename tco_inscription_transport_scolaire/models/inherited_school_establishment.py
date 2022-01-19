# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of odoo
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class InheritedTransportEstablishment(models.Model):
    u"""Surcharge du model school establishment pour y ajouter des données."""

    # region Private attributes
    _inherit = 'horanet.school.establishment'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    station_ids = fields.Many2many(
        string='Stations',
        comodel_name='tco.transport.station')
    stop_ids = fields.Many2many(
        string="Stops",
        comodel_name='tco.transport.stop',
        compute='compute_transport_stops',
        store=True)
    line_exclusive = fields.Boolean(
        string="Exclusive lines",
        help="If you check this box, only lines with the same school cycles will be selected when creating an "
             "inscription.")
    # endregion

    # region Fields method
    @api.depends('station_ids')
    def compute_transport_stops(self):
        """Compute list of stops from stations."""
        for rec in self:
            if rec.station_ids:
                stops_ids = self.env['tco.transport.stop'].search([('station_id', 'in', rec.station_ids.ids)])
                rec.stop_ids = stops_ids
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
