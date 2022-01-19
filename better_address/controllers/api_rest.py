from odoo import http, _
from odoo.http import request, Response
from odoo.osv.expression import get_unaccent_wrapper, normalize_domain

try:
    from odoo.addons.horanet_web.tools.route import jsonRoute, make_error
except ImportError:
    from horanet_web.tools.route import jsonRoute, make_error


class BetterAddressApiRest(http.Controller):
    """Controller to define Rest API routes."""

    @http.route(['/public/horanet/address/country'], type='json', auth='public', website=True)
    def get_countries(self, term=None, domain=None, fields=None, limit=20):
        """Get the countries from REST API.

        :param unicode optional term: Term to search on fields [name]
        :param list optional domain: Domain list to filter query search
        :param list fields: Fields list to filter result
        :param int limit: Result limit number
        :param bool recursive: Specify if the model have to be sent with sub models or just ids
        :return: list of country
        """
        term, domain, fields, errors = self._check_args(term, domain, fields)

        if errors:
            return self._send_error(', '.join(errors))

        domain += [
            ('name', '=ilike', '%' + term + '%'),
        ]

        countries = request.env['res.country'].sudo().search(domain, limit=limit)

        result = []
        for country in countries:
            result.append(self._format_country(country, fields))

        return {
            'length': len(result),
            'records': result
        }

    @http.route(['/public/horanet/address/state'], type='json', auth='public', website=True)
    def get_states(self, term=None, domain=None, fields=None, limit=20, recursive=False):
        """Get the states from REST API.

        :param str optional term: Term to search on fields [name]
        :param list optional domain: Domain list to filter query search
        :param list fields: Fields list to filter result
        :param int limit: Result limit number
        :param bool recursive: Specify if the model have to be sent with sub models or just ids
        :return: list of state
        """
        term, domain, fields, errors = self._check_args(term, domain, fields)

        if errors:
            return self._send_error(', '.join(errors))

        domain += [
            ('name', '=ilike', '%' + term + '%'),
        ]

        states = request.env['res.country.state'].sudo().search(domain, limit=limit)

        result = []
        for state in states:
            result.append(self._format_state(state, fields, recursive))

        return {
            'length': len(result),
            'records': result
        }

    @jsonRoute([  # noqa: C901 - Complexité à 16
        '/api/v1/public/horanet/address/city',
        '/api/v1/public/horanet/address/city/<any(help,):help>',
    ], auth='public', methods=['POST'])
    def api_v1_get_cities(self, term=None, zip_code=False, country_id=False, country_state_id=False,
                          limit=20, recursive=False, fuzzy=True, fields=None, **kwargs):
        u"""Recherche de villes référentielles.

        Exemple:

        {
            "params": {
                "term": "fontenay le comte",
                "zip_code": "0",
                "limit": 20,
                "country_id": 76,
                "country_state_id": 737,
                "recursive": true
            }
        }
        :param unicode term: Term to search on city name
        :param str/int zip_code:
        If string search cities with zip containing 'zip' parameter.
        If integer, search cities with specified zip record (zip = id).
        :param int country_id: ID of city's country.
        :param int country_state_id: ID of city's country state.
        :param list fields: Fields list to filter result
        :param int limit: optional, Result limit number (default=20)
        :param bool fuzzy: optional default=True, If fuzzy == True, the city search by name will be fuzzy, thereby
        the search will by typo proof. Ex : "fontenay le conte" will match with "FONTENAY-LE-COMTE".
        :param bool recursive: Specify if the model have to be sent with sub models or just ids
        :return: list of city
        """
        # Affichage de la docstring (si demande d'aide)
        if 'help' in kwargs:
            return Response(self.api_v1_get_cities.__doc__)

        if not term and (country_id or zip_code or country_state_id):
            term = '%'

        if not term:
            return make_error(_("Missing the argument 'term'"), 400)

        term, domain, fields, errors = self._check_args(term, [], fields)

        cr = request.env.cr
        unaccent = get_unaccent_wrapper(cr)

        if errors:
            return make_error(', '.join(errors), 400)

        # Pourquoi écrire le SQL manuellement au lieu de passer par l'ORM ? -> afin d'éviter dans le
        # cas d'une recherche non 'fuzzy' d'avoir un clause order by (obligatoire via l'ORM), et ainsi
        # de gagner en performance
        query = "SELECT city.id FROM res_city as city"
        domain = [('state', '=', 'confirmed')]
        query_params = []
        order_by_clause = ''
        search_orm = True if len(term) >= 3 and fuzzy else False

        # gestion du filtre ZIP
        if zip_code and isinstance(zip_code, (str, int)):
            if isinstance(zip_code, str):
                if search_orm:
                    domain.append(('zip_ids.name', 'ilike', zip_code))
                else:
                    query += """
                    INNER JOIN res_city_res_zip_rel as rel ON rel.res_city_id = city.id
                    INNER JOIN res_zip as zip ON rel.res_zip_id = zip.id
                    AND {zip_name} ilike {term}
                    WHERE city.state='confirmed'""".format(zip_name=unaccent('zip.name'), term=unaccent('%s'))
                    query_params.append('%' + zip_code + '%')
            else:
                if search_orm:
                    domain.append(('zip_ids', 'in', [zip_code]))
                else:
                    query += """
                        INNER JOIN res_city_res_zip_rel as rel ON rel.res_city_id = city.id
                        AND rel.res_zip_id = %s WHERE city.state='confirmed'"""
                    query_params.append(zip_code)

        # gestion du filtre city name
        if search_orm:
            domain.append(('name', '%', term))
            # cursor.mogrify is just a manual invocation of exactly the same logic that psycopg2
            # uses when it interpolates parameters into the SQL string its self, before it sends it to the server.
            # so, the next statement is SQL injection safe
            order_by_clause = cr.mogrify("similarity(res_city.name, %s) DESC", (term,))
        else:
            query += " AND {name} ilike {term}".format(name=unaccent('city.name'), term=unaccent('%s'))
            query_params.append(term + '%')

        # gestion du filtre Pays
        if country_id and isinstance(country_id, int):
            if search_orm:
                domain.append(('country_id', '=', country_id))
            else:
                query += " AND country_id = %s"
                query_params.append(country_id)

        # gestion du filtre Département
        if country_state_id and isinstance(country_state_id, int):
            if search_orm:
                domain.append(('country_state_id', '=', country_state_id))
            else:
                query += " AND country_state_id = %s"
                query_params.append(country_state_id)

        if search_orm:
            cities = request.env['res.city'].sudo().search(domain, limit=limit, order=order_by_clause)
        else:
            query += " LIMIT %s"
            query_params.append(limit)
            cr.execute(query, query_params)
            search_ids = map(lambda x: x[0], cr.fetchall())
            cities = request.env['res.city'].sudo().browse(search_ids)

        result = []
        for city in cities:
            result.append(self._format_city(city, fields, recursive))

        return {
            'length': len(result),
            'records': result
        }

    @http.route(['/public/horanet/address/zip'], type='json', auth='public', website=True)
    def get_zips(self, term=None, domain=None, fields=None, limit=20):
        """Get the zips from REST API.

        :param str term: Term to search on fields [name]
        :param list optional domain: Domain list to filter query search
        :param list fields: Fields list to filter result
        :param int limit: Result limit number
        :return: list of zip
        """
        if not term:
            return self._send_error(_("Missing the argument 'term'"))

        term, domain, fields, errors = self._check_args(term, domain, fields)

        if errors:
            return self._send_error(', '.join(errors))

        domain += [
            ('name', '=ilike', '%' + term + '%'),
        ]
        # Ne proposer que les éléments d'adresse confirmés
        domain = [('state', '=', 'confirmed')] + domain

        zips = request.env['res.zip'].sudo().search(domain, limit=limit)

        result = []
        for zip_rec in zips:
            result.append(self._format_zip(zip_rec, fields))

        return {
            'length': len(result),
            'records': result
        }

    @jsonRoute([
        '/api/v1/public/horanet/address/street',
        '/api/v1/public/horanet/address/street/<any(help,):help>',
    ], auth='public', methods=['POST'])
    def api_v1_get_streets(self, term=None, city=False, limit=20, fuzzy=True, fields=None, recursive=False, **kw):
        u"""Recherche de rues référentielles.

        Exemple:

        {
            "params": {
                "term": "brisot",
                "city": "fontenay",
                "fuzzy": true,
                "limit": 20,
                "recursive": true
            }
        }

        :param unicode term: Term to search on the street name
        :param list fields: Fields list to filter result
        :param int limit: optional, Result limit number (default=20)
        :param bool fuzzy: optional default=True, If fuzzy == True, the city search by name will be fuzzy, thereby
        the search will by typo proof. Ex : "fontenay le conte" will match with "FONTENAY-LE-COMTE".
        :param bool recursive: Specify if the model have to be sent with sub models or just ids
        :param  str/int city:
        If string search street with city containing 'zip' parameter.
        If integer, search street with specified city record (city_id = id).
        :return: list of street
        """
        # Affichage de la docstring (si demande d'aide)
        if 'help' in kw:
            return Response(self.api_v1_get_cities.__doc__)

        if not term and city:
            term = '%'
        if not term:
            return make_error(_("Missing the argument 'term'"), 400)

        term, domain, fields, errors = self._check_args(term, [], fields)
        if errors:
            return self._send_error(', '.join(errors))

        # Pourquoi écrire le SQL manuellement au lieu de passer par l'ORM ? -> afin d'éviter dans le
        # cas d'une recherche non 'fuzzy' d'avoir un clause order by (obligatoire via l'ORM), et ainsi
        # de gagner en performance
        query = "SELECT street.id FROM res_street as street"
        domain = [('state', '=', 'confirmed')]
        query_params = []
        order_by_clause = ''
        search_orm = True if len(term) >= 3 and fuzzy else False
        cr = request.env.cr
        unaccent = get_unaccent_wrapper(cr)

        # gestion du filtre ville
        if city and isinstance(city, (str, int)):
            if isinstance(city, str):
                if search_orm:
                    domain.append(('city_id.name', 'ilike', city))
                else:
                    query += """
                    INNER JOIN res_city as city ON street.city_id = city.id
                    AND {city_name} ilike {term}
                    WHERE street.state='confirmed'""".format(city_name=unaccent('city.name'), term=unaccent('%s'))
                    query_params.append('%' + city + '%')
            else:
                if search_orm:
                    domain.append(('city_id', '=', city))
                else:
                    query += """ WHERE city_id = %s AND street.state='confirmed'"""
                    query_params.append(city)

        # gestion du filtre street name
        if search_orm:
            domain.append(('name', '%', term))
            # cursor.mogrify is just a manual invocation of exactly the same logic that psycopg2
            # uses when it interpolates parameters into the SQL string its self, before it sends it to the server.
            # so, the next statement is SQL injection safe
            order_by_clause = cr.mogrify("similarity(res_street.name, %s) DESC", (term,))
        else:
            query += " AND {name} ilike {term}".format(name=unaccent('street.name'), term=unaccent('%s'))
            query_params.append('%' + term + '%')

        if search_orm:
            streets = request.env['res.street'].sudo().search(domain, limit=limit, order=order_by_clause)
        else:
            query += " LIMIT %s"
            query_params.append(limit)
            cr.execute(query, query_params)
            search_ids = map(lambda x: x[0], cr.fetchall())
            streets = request.env['res.street'].sudo().browse(search_ids)

        result = []
        for street in streets:
            result.append(self._format_street(street, fields, recursive))

        return {
            'length': len(result),
            'records': result
        }

    @http.route(['/public/horanet/address/street_number'], type='json', auth='public', website=True)
    def get_street_numbers(self, term=None, domain=None, fields=None, limit=20):
        """Get the street numbers from REST API.

        :param str term: Term to search on fields [name]
        :param list optional domain: Domain list to filter query search
        :param list fields: Fields list to filter result
        :param int limit: Result limit number
        :return: list of street_number
        """
        if not term:
            return self._send_error(_("Missing the argument 'term'"))

        new_term, domain, fields, errors = self._check_args(term, domain, fields)

        if errors:
            return self._send_error(', '.join(errors))

        domain += [
            ('name', '=ilike', term + '%')
        ]

        street_numbers = request.env['res.street.number'].sudo().search(domain, limit=limit)

        result = []
        for street_number in street_numbers:
            result.append(self._format_street_number(street_number, fields))

        return {
            'length': len(result),
            'records': result
        }

    @staticmethod
    def _check_args(term=None, domain=None, fields=None):
        """Check args from request.

        :param str term: Term
        :param list domain: Domain
        :param list fields: Fields
        :return: all checked arguments and errors list
        """
        errors = list()
        fields = fields or []

        if not isinstance(fields, list):
            if not isinstance(fields, str):
                errors.append(_("Fields argument must be a list!"))
            fields = [field.strip() for field in fields.split(",")]

        if domain:
            if not isinstance(domain, list):
                errors.append(_("Domain argument must be a list!"))
            domain = normalize_domain(domain)
        else:
            domain = []

        if term:
            term = term.strip()
        else:
            term = '%'

        return term, domain, fields, errors

    @staticmethod
    def _format_country(country, fields=None):
        """Format country for public JSON response.

        :param res.country country: Country to format
        :param list fields: Fields for filtered response
        :return: public JSON response formatted
        """
        result = dict({
            'id': country.id,
        })

        if fields:
            allow_fields = ['name', 'code']
            for field in (x.strip() for x in fields if x in allow_fields):
                result.update({field: country[field]})
        else:
            result.update({
                'name': country.name,
                'code': country.code,
            })

        return result

    def _format_state(self, state, fields=None, recursive=False):
        """Format state for public JSON response.

        :param res.country.state state: State to format
        :param list fields: Fields for filtered response
        :param bool recursive: Recursive response or not
        :return: public JSON response formatted
        """
        result = dict({
            'id': state.id,
        })

        if fields:
            allow_fields = ['name', 'code', 'country_id']
            for field in (x.strip() for x in fields if x in allow_fields):
                if field == 'country_id':
                    result.update({field: self._format_country(state.country_id)})
                else:
                    result.update({field: state[field]})
        else:
            result.update({
                'name': state.name,
                'code': state.code,
                'country_id': self._format_country(state.country_id) if recursive else state.country_id.id,
            })

        return result

    def _format_city(self, city, fields=None, recursive=False):
        """Format city for public JSON response.

        :param dres.city city: City to format
        :param list fields: Fields for filtered response
        :param bool recursive: Recursive response or not
        :return: public JSON response formatted
        """
        result = dict({
            'id': city.id,
        })

        if fields:
            allow_fields = ['name', 'code', 'country_id', 'country_state_id', 'id', 'zip_ids']
            for field in (x.strip() for x in fields if x in allow_fields):
                if field == 'zip_ids':
                    result.update({
                        'zip_ids': [self._format_zip(
                            zip_rec
                        ) for zip_rec in city.zip_ids] if recursive else city.zip_ids.ids
                    })
                elif field == 'country_id':
                    result.update({
                        'country_id': self._format_country(city.country_id) if recursive else city.country_id.id
                    })
                elif field == 'country_state_id':
                    result.update({
                        'country_state_id': self._format_state(
                            city.country_state_id,
                            recursive=False
                        ) if recursive else city.country_state_id.id
                    })
                else:
                    result.update({field: city[field]})
        else:
            result.update({
                'name': city.name,
                'code': city.code,
                'country_id': self._format_country(city.country_id) if recursive else city.country_id.id,
                'country_state_id': self._format_state(
                    city.country_state_id,
                    recursive=False
                ) if recursive else city.country_state_id.id,
                'id': city.id,
                'zip_ids': [self._format_zip(
                    zip_rec
                ) for zip_rec in city.zip_ids] if recursive else city.zip_ids.ids,
            })

        return result

    @staticmethod
    def _format_zip(zip_rec, fields=None):
        """Format zip for public JSON response.

        :param res.zip zip_rec: Zip to format
        :param list fields: Fields for filtered response
        :return: public JSON response formatted
        """
        result = dict({
            'id': zip_rec.id,
        })

        if fields:
            allow_fields = ['name']
            for field in (x.strip() for x in fields if x in allow_fields):
                result.update({field: zip_rec[field]})
        else:
            result.update({
                'name': zip_rec.name,
            })

        return result

    def _format_street(self, street, fields=None, recursive=False):
        """Format street for public JSON response.

        :param res.street street: Street to format
        :param list fields: Fields for filtered response
        :param bool recursive: Recursive response or not
        :return: public JSON response formatted
        """
        result = dict({
            'id': street.id,
        })

        if fields:
            allow_fields = ['name', 'code', 'city_id']
            for field in (x.strip() for x in fields if x in allow_fields):
                if field == 'city_id':
                    result.update({field: self._format_city(street.city_id, recursive=False)})
                else:
                    result.update({field: street[field]})
        else:
            result.update({
                'name': street.name,
                'code': street.name,
                'city_id': self._format_city(
                    street.city_id,
                    recursive=False
                ) if recursive else street.city_id.id,
            })

        return result

    @staticmethod
    def _format_street_number(street_number, fields=None):
        """Format street_number for public JSON response.

        :param res.street.number street_number: Street number to format
        :param list fields: Fields for filtered response
        :return: public JSON response formatted
        """
        result = dict({
            'id': street_number.id,
        })

        if fields:
            allow_fields = ['name']
            for field in (x.strip() for x in fields if x in allow_fields):
                result.update({field: street_number[field]})
        else:
            result.update({
                'name': street_number.name,
            })

        return result

    @staticmethod
    def _send_error(message="Error", code='400'):
        """Format an error response.

        :param unicode optional message: Message for error response
        :param unicode optional code: Code for error response
        :return: Error dict for response
        """
        # Response.status change response status for all next requests too,
        # don't use it and ask for error code in response body to get real error code.
        # Response.status = code
        return {'error': {'code': code, 'message': message}}
