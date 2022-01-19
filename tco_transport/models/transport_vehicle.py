# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class HoranetTransportVehicle(models.Model):
    """Vehicle drive through each stop of a line to carry citizens."""

    # region Private attributes
    _name = 'tco.transport.vehicle'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    license_plate = fields.Char(string='License plate', required=True)
    capacity = fields.Integer(string='Capacity', required=True)
    owner_id = fields.Many2one(string='Owner', comodel_name='res.partner', required=True)
    image = fields.Binary(string='Image')
    driver_id = fields.Many2one(string='Driver', comodel_name='res.partner')
    issuance_date = fields.Date(string='Issuance date')
    acquisition_date = fields.Date(string='Acquisition date')
    vehicle_assignment_ids = fields.One2many(string='Assignments', comodel_name='tco.transport.vehicle.assignment',
                                             inverse_name='vehicle_id')
    service_ids = fields.Many2many(string="Services", comodel_name='tco.transport.service',
                                   compute='compute_vehicle_services', store=True)
    current_service_id = fields.Many2one(string='Current service', compute='_compute_current_service_id',
                                         search='_search_current_service_id', comodel_name='tco.transport.service',
                                         store=False)
    vehicle_model_id = fields.Many2one(string='Model', comodel_name='tco.transport.vehicle.model')
    vehicle_category = fields.Char(string='Category', related='vehicle_model_id.vehicle_category_id.name')
    vehicle_brand = fields.Char(string='Brand', related='vehicle_model_id.vehicle_brand_id.name')
    terminal_ids = fields.Many2many(string='Terminals', comodel_name='tco.terminal', compute='_compute_terminal_ids',
                                    search='_search_terminal_ids')
    # endregion

    # region Fields method
    @api.depends('vehicle_assignment_ids')
    def compute_vehicle_services(self):
        """Compute services of a vehicle form its assignments."""
        for rec in self:
            if rec.vehicle_assignment_ids:
                rec.service_ids = rec.vehicle_assignment_ids.mapped('service_id')

    @api.depends('vehicle_assignment_ids')
    def _compute_current_service_id(self):
        """Compute the service_id of a vehicle by checking if the assignation is valid."""
        for rec in self:
            current_service_rec = rec.vehicle_assignment_ids.filtered('is_valid')
            rec.current_service_id = current_service_rec and current_service_rec[0].service_id or False

    def _search_current_service_id(self, operator, value):
        u"""Search the current service.

        :param operator: opérateur de recherche
        :param value: valeur recherchée
        :return: Retourne un domain de recherche correspondant à la recherche sur le champ calculé is_valid
        """
        search_domain = []
        if operator == '=' and value or operator == '!=' and not value:
            liste_vehicle = self.vehicle_assignment_ids.search([('is_valid', '=', True)]).mapped('vehicle_id.id')
            search_domain = [('id', 'in', liste_vehicle)]
        elif operator == '=' and not value or operator == '!=' and value:
            liste_vehicle = self.vehicle_assignment_ids.search([('is_valid', '=', True)]).mapped('vehicle_id.id')
            search_domain = [('id', 'not in', liste_vehicle)]
        return search_domain

    @api.depends()
    def _compute_terminal_ids(self):
        """Compute list of terminal presents in a vehicle."""
        terminal_obj = self.env['tco.terminal']
        for rec in self:
            rec.terminal_ids = terminal_obj.search([('vehicle_id', '=', rec.id)])

    def _search_terminal_ids(self, operator, value):
        u"""Search terminal.

        :param operator: opérateur de recherche
        :param value: valeur recherchée
        :return: Retourne un domain de recherche correspondant à la recherche sur le champ calculé is_valid
        """
        search_domain = []
        if operator == '=' and value or operator == '!=' and not value:
            liste_terminaux = self.terminal_ids.search([('vehicle_id', '!=', False)]).mapped('vehicle_id.id')
            search_domain.append(('id', 'in', liste_terminaux))
        elif operator == '=' and not value or operator == '!=' and value:
            liste_terminaux = self.terminal_ids.search([('vehicle_id', '!=', False)]).mapped('vehicle_id.id')
            search_domain.append(('id', 'not in', liste_terminaux))
    # endregion

    # region Constrains and Onchange
    @api.constrains('license_plate')
    def _check_license_plate(self):
        """Check if license_plate is valid.

        :raise: odoo.exceptions.ValidationError if the field is empty
        """
        for rec in self:
            if len(rec.license_plate.strip()) == 0:
                raise exceptions.ValidationError(_('License plate cannot be empty'))

    @api.constrains('vehicle_assignment_ids')
    def _check_vehicle_assignments(self):
        """Check if there is not an active assignment already on the vehicle."""
        for rec in self:
            active_assignment = rec.mapped('vehicle_assignment_ids').filtered('is_valid')
            if len(active_assignment) > 1:
                raise exceptions.ValidationError(_("You can't add an assignment if there is already an active one."))

    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        """Return the display name of the record."""
        result = []
        for record in self:
            license_plate = record.license_plate.strip()
            name = ''
            if len(license_plate) > 1:
                name += license_plate
                if record.vehicle_model_id.name:
                    name += ' ' + record.vehicle_model_id.name
                if record.vehicle_brand:
                    name += ' ' + record.vehicle_brand
            result.append((record.id, name))
        return result

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
