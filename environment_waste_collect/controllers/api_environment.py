# coding: utf-8
import json

from odoo import http
from odoo.http import Response
from odoo.http import request

try:
    from odoo.addons.horanet_subscription.controller import tools
    from odoo.addons.horanet_web.tools import route
except ImportError:
    from horanet_subscription.controller import tools
    from horanet_web.tools import route


class APIEnvironmentController(http.Controller):
    u"""Api de gestion de l'environment."""

    @route.jsonRoute([
        '/api/v1/device/environment/wastesite/<int:waste_site_id>/configuration',
        '/api/v1/device/environment/wastesite/<int:waste_site_id>/configuration<any(help,):help>'],
        methods=['GET'], auth='none', csrf=False)
    @tools.device_route
    def api_device_get_waste_site_configuration(self, waste_site_id, **post):
        u"""Api de récupération de la configuration des déchetteries.

        Exemple de configuration de déchetterie :
        {
            "devices":
            [
                "barriers":
                [
                    "type":"ENTER",
                    "id":115,
                    "name":"barrier name",
                    "address_ip":"124.12.313.234"
                ],
                "displays":
                [
                    "name":"display name",
                    "address_ip":"124.123.13.234"
                ],
                "cameras":
                [
                    "name":"camera name",
                    "address_ip":"124.123.1.234"
                ],
            ]
        }

        la réponse est de la forme :

        {
            "name": "Déchèterie Guiers – Domessin",
            "id": 1,
            "configuration" :{<CONFIG JSON>},
        }

        :param waste_site_id: The waste site on which the configuration will be sent (int)
        """
        # Affichage de la docstring (si demande d'aide)
        if 'help' in post:
            return Response(self.api_v1_device_environment_pickup_requests.__doc__)

        # Recherche de la déchetterie
        waste_site_rec = request.env['environment.waste.site'].sudo().browse(waste_site_id)
        if not waste_site_rec:
            return route.make_error('Waste site with id ' + str(waste_site_id) + ' not found', 400)

        def is_json(json_string):
            u"""Test si la chaîne est JSON valide."""
            try:
                json.loads(json_string)
            except ValueError:
                return False
            return True

        if waste_site_rec.configuration_json and not is_json(waste_site_rec.configuration_json):
            return route.make_error("The configuration is not JSON serializable", 456)

        response_body = json.dumps(
            {
                'id': waste_site_rec.id,
                'name': waste_site_rec.name,
                'configuration': json.loads(waste_site_rec.configuration_json)
            })
        return http.Response(
            response=response_body,
            status=200,
            headers=[('Content-Type', 'application/json'), ('Content-Length', len(response_body))]
        )
