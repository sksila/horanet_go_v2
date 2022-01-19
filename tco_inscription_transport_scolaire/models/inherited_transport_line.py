# -*- coding: utf-8 -*-

# 2 :  imports of odoo
from odoo import models, api, fields


class InheritedTransportLine(models.Model):
    """Surcharge du model tco.transport.line pour y ajouter un champ places disponibles."""

    # region Private attributes
    _inherit = 'tco.transport.line'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    remaining_places = fields.Integer(
        string="Remaining places",
        compute='compute_remaining_places',
        search='_search_line_by_remaining_places')
    vehicle_occupation = fields.Integer(
        string="Vehicle occupation",
        compute='compute_vehicle_occupation',
        search='_search_by_vehicle_occupation',
        help="Occupation is computed based on the latest school period.")
    school_cycle_ids = fields.Many2many(
        string="School cycles",
        comodel_name='horanet.school.cycle')

    # endregion

    # region Fields method
    @api.depends('service_id')
    def compute_remaining_places(self):
        u"""Méthode qui va appeler le calcul du nombre de places restantes."""
        for rec in self:
            if rec.service_id:
                rec.remaining_places = self.get_remaining_places(rec)

    def _search_line_by_remaining_places(self, operator, value):
        """
        Search line by remaining places.

        :param operator: operator
        :param value: int
        :return: domain
        """
        lines = self.env['tco.transport.line']
        if isinstance(value, int) and operator in ['=', '>', '>=', '<', '<=']:
            assignments = self.env['tco.transport.vehicle.assignment'].search([('vehicle_id', '!=', False)])
            last_period = self.env['tco.inscription.period'].search([], order='date_end desc', limit=1)
            for assignment in assignments:
                eligible_lines = assignment.service_id.line_ids
                default_places = assignment.vehicle_id.capacity
                # On compte les inscriptions ayant pour ligne aller ou retour celles qui composent le service
                # de l'assignation
                inscriptions_count = self.env['tco.inscription.transport.scolaire']\
                    .search_count([('period_id', '=', last_period.id),
                                   '|',
                                   ('line_forward_id', 'in', eligible_lines.ids),
                                   ('line_backward_id', 'in', eligible_lines.ids)])
                remaining_places = default_places - inscriptions_count
                if operator == '=' and remaining_places == value:
                    lines += eligible_lines
                elif operator == '>' and remaining_places > value:
                    lines += eligible_lines
                elif operator == '>=' and remaining_places >= value:
                    lines += eligible_lines
                elif operator == '<' and remaining_places < value:
                    lines += eligible_lines
                elif operator == '<=' and remaining_places <= value:
                    lines += eligible_lines

        domain = [('id', 'in', lines.ids)]

        return domain

    @api.depends('service_id')
    def compute_vehicle_occupation(self):
        """Compute the vehicle occupation for a line."""
        for rec in self:
            assignment_model = self.env['tco.transport.vehicle.assignment']
            if not rec.remaining_places:
                self.get_remaining_places(rec)

            assignment = assignment_model.search([('service_id', '=', rec.service_id.id), ('is_valid', '=', True)])
            vehicle = assignment and assignment.vehicle_id if len(assignment) == 1 else False
            if vehicle:
                occupation = int(round(((vehicle.capacity - rec.remaining_places) / float(vehicle.capacity)) * 100))
                rec.vehicle_occupation = occupation
            else:
                rec.vehicle_occupation = 999

    def _search_by_vehicle_occupation(self, operator, value):
        """
        Search line by vehicle occupation.

        :param operator: operator
        :param value: int
        :return: domain
        """
        lines = self.env['tco.transport.line']

        if isinstance(value, int) and operator in ['>', '>=', '<', '<=']:
            assignments = self.env['tco.transport.vehicle.assignment'].search([('vehicle_id', '!=', False)])
            last_period = self.env['tco.inscription.period'].search([], order='date_end desc', limit=1)
            for assignment in assignments:
                eligible_lines = assignment.service_id.line_ids
                default_places = assignment.vehicle_id.capacity
                # On compte les inscriptions ayant pour ligne aller ou retour celles qui composent le service
                # de l'assignation
                inscriptions_count = self.env['tco.inscription.transport.scolaire'] \
                    .search_count([('period_id', '=', last_period.id),
                                   '|',
                                   ('line_forward_id', 'in', eligible_lines.ids),
                                   ('line_backward_id', 'in', eligible_lines.ids)])
                vehicle_occupation = int(round((inscriptions_count / float(default_places)) * 100))
                if operator == '>' and vehicle_occupation > value:
                    lines += eligible_lines
                elif operator == '>=' and vehicle_occupation >= value:
                    lines += eligible_lines
                elif operator == '<' and vehicle_occupation < value:
                    lines += eligible_lines
                elif operator == '<=' and vehicle_occupation <= value:
                    lines += eligible_lines

        domain = [('id', 'in', lines.ids)]

        return domain
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        """Surcharge du name_get pour afficher le nombre de places disponibles en plus dans le nom du champ."""
        res = []
        for line in self:
            res.append((line.id, unicode(line.name)))
        return res

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def get_remaining_places(self, line_id):
        """Calcul le nombre de places restantes.

        :param line_id: la ligne
        :return: le nombre de places restantes ou 999
        """
        inscription_model = self.env['tco.inscription.transport.scolaire']
        assignment_model = self.env['tco.transport.vehicle.assignment']
        assignment = self.env['tco.transport.vehicle.assignment']
        # On vérifie si la ligne a un service valide
        if line_id.service_id:
            assignment = assignment_model.search([('service_id', '=', line_id.service_id.id), ('is_valid', '=', True)])
        # Ensuite on vérifie si elle est assignée et qu'elle a un véhicule
        if len(assignment) == 1 and assignment.vehicle_id:
            default_places = assignment.vehicle_id.capacity
            last_period = self.env['tco.inscription.period'].search([], order='date_end desc', limit=1)
            # On compte par rapport à la dernière période d'inscription scolaire
            inscriptions_count = inscription_model.search_count([('period_id', '=', last_period.id),
                                                                 '|',
                                                                 ('line_forward_id', '=', line_id.id),
                                                                 ('line_backward_id', '=', line_id.id)
                                                                 ])

            return default_places - inscriptions_count
        # Si la ligne n'est pas assignée ou n'a pas de véhicule ou qu'il y a plusieurs assignation, on renvoi 999
        else:
            return 999

    # endregion

    pass
