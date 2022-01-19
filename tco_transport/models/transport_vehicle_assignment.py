# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HoranetTransportVehicleAssignment(models.Model):
    """Attach a vehicle to a service for certain amout of time."""

    # region Private attributes
    _name = 'tco.transport.vehicle.assignment'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    vehicle_id = fields.Many2one(
        string='Vehicle',
        comodel_name='tco.transport.vehicle',
        required=True,
    )
    service_id = fields.Many2one(
        string='Service',
        comodel_name='tco.transport.service',
        required=True
    )

    begin_date = fields.Date(string='Begin date')
    end_date = fields.Date(string='End date')
    is_valid = fields.Boolean(
        string='Is valid',
        compute='_compute_is_valid',
        search='_search_is_valid',
        store=False
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.depends('begin_date', 'end_date')
    def _compute_is_valid(self):
        """Check if the assignation of a vehicle is valid."""
        for rec in self:
            is_valid = True
            if rec.begin_date and rec.begin_date > fields.Date.today():
                is_valid = False
            elif rec.end_date and rec.end_date < fields.Date.today():
                is_valid = False

            rec.is_valid = is_valid

    def _search_is_valid(self, operator, value):
        current_date = fields.Date.today()
        search_domain = []

        if (operator == '=' and value is True) or (operator == '!=' and value is False):
            search_domain = [
                '&',
                '|', ('begin_date', '=', False), ('begin_date', '<=', current_date),
                '|', ('end_date', '=', False), ('end_date', '>=', current_date)
            ]
        elif (operator == '=' and value is False) or (operator == '!=' and value is True):
            search_domain = [
                '!',
                '&',
                '|', ('begin_date', '=', False), ('begin_date', '<=', current_date),
                '|', ('end_date', '=', False), ('end_date', '>=', current_date)
            ]
        return search_domain

    # endregion

    pass
