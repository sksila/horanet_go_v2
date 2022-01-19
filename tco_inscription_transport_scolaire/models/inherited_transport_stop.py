# -*- coding: utf-8 -*-

# 2 :  imports of odoo
from odoo import models, api


class InheritedTransportStop(models.Model):
    u"""Surcharge du model tco.transport.stop pour y ajouter un name_search et un name_get."""

    # region Private attributes
    _inherit = 'tco.transport.stop'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=10):
        u"""Surcharge du name_search pour rechercher les stops en fonction de la station et des lignes."""
        if args is None:
            args = []

        context = self.env.context
        ids = []

        if context.get('special_search', False):
            # # On tri par heure décroissante ou croissante
            order = 'stop_time desc' if context.get('order', False) else 'stop_time'
            establishment = self.env['horanet.school.establishment'].browse(context.get('establishment_id'))

            # On prends les stations de l'établissement et ses arrêts
            etab_stations = establishment.station_ids
            etab_stops = self.search([('station_id', 'in', etab_stations.ids)])

            # On traite soit le trajet retour, soit l'aller
            if context.get('return', False):
                # On prend tous les arrêts situés après ceux de l'établissement
                stops = etab_stops.mapped('next_stops_ids') + etab_stops
                domain = [('id', 'in', stops.ids)]
                if name and name.isdigit():
                    domain.append(('stop_time', '>=', int(name)))
                    domain.append(('stop_time', '<=', int(name) + 1))
                # On va chercher ces arrêts avec un search pour prendre en compte le domaine sur le champ
                stops = self.search([('line_id.line_type', '=', 'return'), ('line_id.is_active_on_monday', '=', True)]
                                    + domain + args, limit=limit,
                                    order=order)
            else:
                # On prend tous les arrêts situés avant ceux de l'établissement
                stops = etab_stops.mapped('previous_stops_ids') + etab_stops
                # On va chercher ces arrêts avec un search pour prendre en compte le domaine sur le champ
                stops = self.search([('id', 'in', stops.ids), ('line_id.line_type', '=', 'outward'),
                                     ('line_id.is_active_on_monday', '=', True)] + args, limit=limit,
                                    order=order)

            # Si on ne veut que des lignes avec des cycles scolaires spécifiques
            if establishment.line_exclusive:
                stops = stops.filtered(lambda r: r.line_id.school_cycle_ids >= establishment.computed_school_cycle)

            ids = stops
            if ids:
                res = []
                for results in self.browse(ids.ids):
                    # On formate l'heure
                    time = '{0:02.0f}:{1:02.0f}'.format(*divmod(results.stop_time * 60, 60))
                    remaining_places = self.env['tco.transport.line'].get_remaining_places(results.line_id)
                    res.append((results.id, unicode(time) + " " + unicode(results.line_id.name) +
                                " (" + unicode(remaining_places) + ")"))
                # On retourne la liste
                return res
            # Sinon on retourne rien
            else:
                return []
        # Si pas de contexte, alors recherche classique
        else:
            return super(InheritedTransportStop, self).name_search(name, args, operator=operator, limit=limit)

    @api.multi
    def name_get(self):
        u"""Surcharge du name_get pour afficher l'heure en plus dans le nom du champ."""
        res = []
        for stop in self:
            time = '{0:02.0f}:{1:02.0f}'.format(*divmod(stop.stop_time * 60, 60))
            remaining_places = self.env['tco.transport.line'].get_remaining_places(stop.line_id)
            res.append((stop.id, unicode(time) + " " + unicode(stop.line_id.name) +
                        " (" + unicode(remaining_places) + ")"))
        return res
        # endregion

        # region Actions
        # endregion

        # region Model methods
        # endregion

    pass
