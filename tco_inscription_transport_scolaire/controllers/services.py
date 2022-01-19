# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class WebsiteAccount(http.Controller):
    """Contains function related to derogation and establishment."""

    @http.route(['/horanet/get_is_derogation'], type='json', auth='user', website=True)
    def getDerogation(self, school_establishment_id=None, partner_id=None, **kwargs):
        """Get the derogation if needed.

        :return: derogation
        """
        if not school_establishment_id or not partner_id:
            # Response.status change response status for all next requests too,
            # don't use it and ask for error code in response body to get real error code.
            # Response.status = "400 Bad request"
            return {'error': {'code': 400, 'message': "Missing arguments"}}

        inscription_model = request.env['tco.inscription.transport.scolaire']
        partner_rec = request.env['res.partner'].browse(int(partner_id))
        establishment_rec = request.env['horanet.school.establishment'].browse(int(school_establishment_id))
        return inscription_model.get_is_derogation(establishment_rec, partner_rec)

    @http.route(['/horanet/search/establishments'], type='json', auth='user', website=True)
    def get_establishment(self, term=None, limit=20, domain=None, **kwargs):
        u"""Get the establishments.

        Méthode permettant au frontend de récupérer les information relative à un établissement et de sa ville liée
        si elle existe en une seule requête.

        :param term: le terme de recherche
        :param limit: le nombre d'élément à retourner (max)
        :param domain: domain de recherche (optionel)
        :param kwargs: optionel
        :return: un dictionaire avec pour chaque établissement : name, code, id, city_id et city_name
        """
        if not term and not domain:
            # Response.status change response status for all next requests too,
            # don't use it and ask for error code in response body to get real error code.
            # Response.status = "400 Bad request"
            return {'error': {'code': 400, 'message': "Missing the argument 'term'"}}

        horanet_establishment = request.env['horanet.school.establishment'].sudo()

        domain = domain or []
        domain.append(('name', 'ilike', unicode(term)))

        establishments = horanet_establishment.search(domain, limit=limit)

        result = []
        for establishment in establishments:
            result.append({'name': establishment.name,
                           'code': establishment.code,
                           'city_name': establishment.city_id and establishment.city_id.name or '',
                           'city_id': establishment.city_id.id,
                           'id': establishment.id
                           })

        # tri de la liste des résultats selon la taille de la chaîne (approximation de "best match")
        result.sort(key=lambda e: e['name'])

        return result
