from odoo import http
from odoo.http import request


class WebsiteAccount(http.Controller):
    """Class of services controller."""

    @http.route(['/horanet/search/cities'], type='json', auth='user', website=True)
    def get_cities(self, term=None, limit=20, domain=None, **kwargs):
        """Get the cities."""
        if not term and not domain:
            # Response.status change response status for all next requests too,
            # don't use it and ask for error code in response body to get real error code.
            # Response.status = "400 Bad request"
            return {'error': {'code': 400, 'message': "Missing the argument 'term'"}}

        res_city = request.env['res.city'].sudo()

        domain = domain or []

        if term and term.isdigit():
            domain.append(('zip_ids.name', '=ilike', unicode(term) + '%'))
        elif term:
            domain.append(('name', 'ilike', unicode(term)))

        cities = res_city.search(domain, limit=limit)

        result = []
        for city in cities:
            result.append({'name': city.name,
                           'code': city.code,
                           'country': {'id': city.country_id.id, 'name': city.country_id.name},
                           'country_state': {'id': city.country_state_id.id, 'name': city.country_state_id.name},
                           'id': city.id,
                           'zip_codes': [{'id': zip.id, 'code': zip.name} for zip in city.zip_ids],
                           })

        # tri de la liste des réultats selon la taille de la chaine (approximation de "best match")
        result.sort(key=lambda ville: len(ville['name']))

        return result
