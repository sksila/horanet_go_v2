# -*- coding: utf-8 -*-

import operator as pyoperator
# 1 : imports of python lib
from math import radians, cos, sin, asin, sqrt

# 2 :  imports of odoo
from odoo import models, api, fields


class InheritedTransportStation(models.Model):
    """Surcharge du model tco.transport.station pour y ajouter un name_search."""

    # region Private attributes
    _inherit = 'tco.transport.station'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    service_ids = fields.Many2many(string="Services", comodel_name='tco.transport.service',
                                   compute='_compute_station_services', search='_search_station_by_service')
    # endregion

    # region Fields method
    @api.depends()
    def _compute_station_services(self):
        """Compute all the services for a station."""
        for rec in self:
            stops = self.env['tco.transport.stop'].search([('station_id', '=', rec.id)])
            services = self.env['tco.transport.service'].search([('line_ids', 'in', stops.mapped('line_id.id'))])
            rec.service_ids = services.ids

    def _search_station_by_service(self, operator, value):
        """
        Search station by service.

        :param operator: operator
        :param value: int or char
        :return: domain
        """
        # On retourne un domaine qui renvoi du vide par défaut
        domain = [('id', '=', False)]

        if isinstance(value, list) and operator == 'in':
            services = self.env['tco.transport.service'].search([('id', 'in', value)])
            lines = self.env['tco.transport.line'].search([('service_id', 'in', services.ids)])
            stations = lines and lines.mapped('line_stop_ids.station_id')
            if stations:
                domain = [('id', 'in', stations.ids)]

            return domain
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=20):
        u"""Surcharge du name_search pour rechercher les stations par proximité."""
        if args is None:
            args = []

        context = self.env.context
        station_ids = []
        sorted_stations = []

        if context.get('special_search', False) and context.get('partner_id', False) \
                and context.get('establishment_id', False):
            recipient = self.env['res.partner'].browse(context.get('partner_id'))
            if recipient:
                if recipient.street_id and recipient.city_id and recipient.state_id and recipient.zip_id:
                    # Si le partner n'est pas encore géolocalisé, alors on le fait.
                    if not recipient.partner_longitude and not recipient.partner_latitude:
                        recipient.geo_localize()

                    establishment = self.env['horanet.school.establishment'].browse(context.get('establishment_id'))

                    # On prends les stations de l'établissement et ses arrêts
                    etab_stations = establishment.station_ids
                    etab_stops = self.env['tco.transport.stop'].search([('station_id', 'in', etab_stations.ids)])

                    # On fait une recherche soit pour les lignes retour, soit aller
                    if context.get('return', False):
                        # On va chercher tous les arrêts après celui de l'établissement sur la même ligne
                        domain = [('id', 'in', etab_stops.mapped('next_stops_ids').ids),
                                  ('line_id.line_type', '=', 'return'),
                                  ('line_id.is_active_on_monday', '=', True)]
                        if name:
                            domain.append(('station_id.name', 'ilike', name))
                        stops = self.env['tco.transport.stop'].search(domain) + etab_stops
                        # stops = etab_stops.mapped('next_stops_ids').filtered(
                        #     lambda r: r.line_id.line_type == 'return' and r.line_id.is_active_on_monday) + etab_stops
                        # Si on ne veut que des lignes avec des cycles scolaires spécifiques
                        if establishment.line_exclusive:
                            stops = stops.filtered(
                                lambda r: r.line_id.school_cycle_ids >= establishment.computed_school_cycle)
                        # On prend ensuite les stations de ces arrêts
                        stations = stops.mapped('station_id').filtered(lambda r: r.latitude and r.longitude)
                    else:
                        # On va chercher tous les arrêts avant celui de l'établissement sur la même ligne
                        domain = [('id', 'in', etab_stops.mapped('previous_stops_ids').ids),
                                  ('line_id.line_type', '=', 'outward'),
                                  ('line_id.is_active_on_monday', '=', True)]
                        if name:
                            domain.append(('station_id.name', 'ilike', name))
                        stops = self.env['tco.transport.stop'].search(domain) + etab_stops
                        # Si on ne veut que des lignes avec des cycles scolaires spécifiques
                        if establishment.line_exclusive:
                            stops = stops.filtered(
                                lambda r: r.line_id.school_cycle_ids >= establishment.computed_school_cycle)
                        # On prend ensuite les stations de ces arrêts
                        stations = stops.mapped('station_id').filtered(lambda r: r.latitude and r.longitude)

                    # On va calculer la distance entre le lieu d'habitation géolocalisé et la station
                    distance = {}
                    for station in stations:
                        slon, slat, plon, plat = map(radians, [station.longitude, station.latitude,
                                                               recipient.partner_longitude, recipient.partner_latitude])
                        # haversine formula
                        dlon = plon - slon
                        dlat = plat - slat
                        a = sin(dlat / 2) ** 2 + cos(slat) * cos(plat) * sin(dlon / 2) ** 2
                        c = 2 * asin(sqrt(a))
                        dist_km = 6367 * c
                        distance[station.id] = int(round(dist_km * 1000, 0))

                    # On trie par distance croissante
                    sorted_stations = sorted(distance.items(), key=pyoperator.itemgetter(1))

                    # On ajoute les 10 premiers dans ids
                    for station in sorted_stations[:10]:
                        station_ids.append(station[0])
            if station_ids:
                res = []
                for results in self.browse(station_ids):
                    res.append((results.id, unicode(results.name) + ", " +
                                unicode(sorted_stations[station_ids.index(results.id)][1]) + "m"))
                # On retourne la liste
                return res
            # Sinon on retourne rien
            else:
                return []

        # Si pas de contexte, alors recherche classique
        else:
            return super(InheritedTransportStation, self).name_search(name, args, operator=operator, limit=limit)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
    pass
