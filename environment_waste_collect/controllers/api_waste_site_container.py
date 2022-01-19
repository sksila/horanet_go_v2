# coding: utf-8

from datetime import datetime

from odoo import http, exceptions
from odoo.http import request, Response

try:
    from odoo.addons.horanet_subscription.controller.tools import device_route
    from odoo.addons.horanet_web.tools.route import jsonRoute, make_error, standard_response
except ImportError:
    from horanet_subscription.controller.tools import device_route
    from horanet_web.tools.route import jsonRoute, make_error, standard_response


class APIWasteContainerController(http.Controller):
    u"""Controller des bennes et emplacement de bennes des déchetteries."""

    @jsonRoute(route=[  # noqa: C901
        '/api/v1/device/environment/pickup_requests/',
        '/api/v1/device/environment/pickup_requests/<int:pickup_request_id>',
        '/api/v1/device/environment/pickup_requests/<int:pickup_request_id>/<any(close,cancel):action>',
        '/api/v1/device/environment/pickup_requests/<any(help,):help>',
    ],
        auth='none', methods=['GET', 'POST'], csrf=False)
    @device_route
    def api_v1_device_environment_pickup_requests(self, pickup_request_id=None, action=None, **kw):
        u"""API de récupération / modification / création des demandes de relève.

        Voir https://www.restapitutorial.com/lessons/httpmethods.html pour les bonnes pratiques

        JSON request content example:

        *  Pour modifier l'état de la demande:
            URL: POST {{odoo_url}}/api/v1/device/environment/pickup_requests/1

            body:
            ```
            {
                "values": {
                    "emplacement_id": 3,
                    "schedule_date": "2018-08-23 13:07:29",
                    "user_name": "Ly Tran"
                },
                "device_id": "{{device_id}}"
            }
            ```
        -  Pour récupérer les informations de relève:
            URL: GET {{odoo_url}}/api/v1/device/environment/pickup_requests/?device_id={{device_id}}

            Paramètres de filtre optionnels:
                -  smarteco_waste_site_id <int>
                -  waste_site_id <int>
                -  last_sync_date (exemple : last_sync_date="2018-08-23 14:55:31")
                -  state <string>[progress,done]

        :param pickup_request_id: optionnel, l'id d'une demande de relève
        :param action: optionnel, l'un des verbes suivant : close,cancel
        :param kw: http parameters
        :return: json body
        """
        pickup_request_rec = None
        # Affichage de la docstring (si demande d'aide)
        if 'help' in kw:
            return Response(self.api_v1_device_environment_pickup_requests.__doc__)
        if pickup_request_id:
            if not isinstance(pickup_request_id, int):
                return make_error("Argument 'pickup_request_id' should be an int, got {bad_type} instead".format(
                    bad_type=str(type(pickup_request_id))), 400)
            pickup_request_rec = request.env['environment.pickup.request'].sudo().browse(pickup_request_id).exists()
            if not pickup_request_rec:
                return make_error("Pickup-request not found", 404)

        # Lecture d'information
        if request.httprequest.method == 'GET':
            # Lecture d'un enregistrement
            if pickup_request_rec:
                return self._get_pickup_request_data(pickup_request_rec)
            search_domain = []
            last_sync_date = kw.get('last_sync_date', None)
            if last_sync_date:
                search_domain.append(('write_date', '>=', last_sync_date))
            state = kw.get('state', None)
            if state:
                search_domain.append(('state', '=', state))
            real_last_sync_date = str(datetime.now())
            if 'smarteco_waste_site_id' in kw:
                waste_site_rec = request.env['environment.waste.site'].sudo().search([(
                    'smarteco_waste_site_id', '=', int(kw['smarteco_waste_site_id']))], limit=1)
                if waste_site_rec:
                    search_domain.append(('waste_site_id', '=', waste_site_rec.id))
                else:
                    make_error("'smarteco_waste_site_id' not found", 404)
            if 'waste_site_id' in kw:
                search_domain.append(('waste_site_id', '=', int(kw['waste_site_id'])))
            pickup_request = request.env['environment.pickup.request'].sudo().search(search_domain)
            return {
                'pickup_requests': self._get_pickup_request_data(pickup_request),
                'real_last_sync_date': real_last_sync_date
            }

        elif request.httprequest.method == 'POST':
            # Création d'une nouvelle demande
            if not pickup_request_id:
                values = kw.get('values', None)
                if not values:
                    return make_error("Missing values dictionary", 400)
                values['created_by'] = values.pop('user_name', None)
                new_pickup_request = request.env['environment.pickup.request'].sudo().create(values)
                return {'pickup_request': self._get_pickup_request_data(new_pickup_request)}

            elif pickup_request_rec and action in ['close', 'cancel']:
                values = kw.get('values', None)
                if not values:
                    return make_error("Missing values dictionary", 400)
                user_name = values.pop('user_name', None)
                if pickup_request_rec.close_date:
                    return make_error("Can't close or cancel a 'done' pickup request", 403)
                try:
                    # Clôture d'une demande
                    if action == 'close':
                        pickup_request_rec.action_close(user_name=user_name)
                    # annulation d'une demande
                    elif action == 'cancel':
                        pickup_request_rec.action_cancel(user_name=user_name)
                    return {'pickup_request': self._get_pickup_request_data(pickup_request_rec)}
                except exceptions.ValidationError as error:
                    return make_error("Validation error: {message}".format(message=unicode(error.name)), 409)
            else:
                return make_error("Bad method", 405)
        return make_error("No response", 500)

    @staticmethod
    def _get_pickup_request_data(pickup_requests):
        u"""Retourne un recordset de relèves de bennes sous forme de data json.

        Utilisé pour factoriser la recherche et le nommage des champs pour l'api des emplacements

        :param pickup_requests: un recordset de relèves (''environment.pickup.request')
        :return: json data
        """
        pickup_requests_data = []
        pickup_requests_data.extend([{
            'id': pickup_request.id,
            'emplacement_id': pickup_request.emplacement_id and pickup_request.emplacement_id.id or False,
            'container_id': pickup_request.container_id and pickup_request.container_id.id or False,
            'state': pickup_request.state,
            'priority': pickup_request.priority,
            'request_date': pickup_request.request_date,
            'schedule_date': pickup_request.schedule_date,
            'validated_by': pickup_request.validated_by,
            'created_by': pickup_request.created_by,
            'write_date': pickup_request.write_date,
            'close_date': pickup_request.close_date,
            'waste_site_id': pickup_request.waste_site_id and pickup_request.waste_site_id.id or False,
        } for pickup_request in pickup_requests])

        return pickup_requests_data

    @jsonRoute(route=[
        '/api/v1/device/environment/emplacements/',
        '/api/v1/device/environment/emplacements/<int:emplacement_id>',
        '/api/v1/device/environment/emplacements/<any(help,):help>',
    ], auth='none', methods=['GET', 'PUT'], csrf=False)
    @device_route
    def api_v1_device_environment_emplacements(self, emplacement_id=None, **kw):
        u"""API de récupération / modification des emplacement de déchetterie.

        Voir https://www.restapitutorial.com/lessons/httpmethods.html pour les bonnes pratiques

        JSON request content example:

        *  Pour modifier le niveau de remplissage:
            URL: PUT {{odoo_url}}/api/v1/device/environment/emplacements/1?device_id={{device_id}}

            body:
            ```
            {
            "filling_level": 50,
            }
            ```
        -  Pour récupérer les informations d'emplacement:
            URL: GET {{odoo_url}}/api/v1/device/environment/emplacements/?device_id={{device_id}}

            Paramètres optionnels:
                -  smarteco_waste_site_id
                -  waste_site_id
                -  last_sync_date

        :param emplacement_id: optionnel, l'id d'un emplacement
        :param kw: http parameters
        :return: json body
        """
        # Affichage de la docstring (si demande d'aide)
        if 'help' in kw:
            return Response(self.api_v1_device_environment_pickup_requests.__doc__)

        emplacement_rec = None
        if emplacement_id:
            if not isinstance(emplacement_id, int):
                return make_error("Argument 'emplacement_id' should be an int, got {bad_type} instead".format(
                    bad_type=str(type(emplacement_id))), 400)
            emplacement_rec = request.env['stock.emplacement'].sudo().browse(emplacement_id).exists()
            if not emplacement_rec:
                return make_error("Emplacement not found", 404)

        if request.httprequest.method == 'PUT':
            if not emplacement_id:
                return make_error("Not allowed to modify the entire collection", 405)
            write_data = {k: kw.get(k, None) for k in ('filling_level',) if k in kw}
            emplacement_rec.write(write_data)
            return {
                'emplacement': self._get_emplacements_data(emplacement_rec)[0]
            }

        if request.httprequest.method == 'GET':
            if emplacement_rec:
                return self._get_emplacements_data(emplacement_rec)
            search_domain = []
            last_sync_date = kw.get('last_sync_date', None)
            if last_sync_date:
                search_domain.append(('write_date', '>=', last_sync_date))
            real_last_sync_date = str(datetime.now())
            if 'smarteco_waste_site_id' in kw:
                search_domain.append(('smarteco_waste_site_id', '=', int(kw['smarteco_waste_site_id'])))
            if 'waste_site_id' in kw:
                search_domain.append(('waste_site_id', '=', int(kw['waste_site_id'])))
            emplacements = request.env['stock.emplacement'].sudo().search(search_domain)
            return {
                'emplacements': self._get_emplacements_data(emplacements),
                'real_last_sync_date': real_last_sync_date
            }

        return make_error("Bad method", 405)

    @staticmethod
    def _get_emplacements_data(emplacements):
        u"""Retourne un recordset d'emplacements sous forme de data json.

        Utilisé pour factoriser la recherche et le nommage des champs pour l'api des emplacements

        :param emplacements: un recordset d'emplacement ('stock.emplacement')
        :return: json data
        """
        emplacement_data = []
        emplacement_data.extend([{
            'id': emplacement.id,
            'waste_site_id': emplacement.waste_site_id and emplacement.waste_site_id.id or False,
            'smarteco_waste_site_id':
                emplacement.waste_site_id and emplacement.waste_site_id.smarteco_waste_site_id or False,
            'activity_id': emplacement.activity_id and emplacement.activity_id.id or False,
            'smarteco_waste_id': emplacement.activity_id and emplacement.activity_id.smarteco_product_id or False,
            'name': emplacement.name,
            'filling_level': emplacement.filling_level,
            'filling_update_date': emplacement.filling_update_date,
            'last_collect_date': emplacement.last_collect_date,
            'create_date': emplacement.create_date
        } for emplacement in emplacements])

        return emplacement_data

    @http.route('/api/v0/device/environment/pickup_requests/create/',
                type='json', auth='none', csrf=False, methods=['POST'])
    @standard_response
    @device_route
    def create_pickup_requests(self, values, user_id, **kw):
        """Create one or more pickup requests given the provided values.

        JSON request content example:
        {
            "params": {
                "context": {},
                "values": [
                    {
                        "emplacement_id": 1,
                        "schedule_date": ""
                    },
                    {
                        "emplacement_id": 2,
                        "schedule_date": ""

                ],
                "user_id": "A name"
            }
        }
        """
        # sudo mode
        request.env.uid = 1

        pickup_request_obj = request.env['environment.pickup.request']

        for value in values:
            value['created_by'] = user_id
            pickup_request_obj.create(value).id

        return True
