from odoo import http
from odoo.http import Controller, request

try:
    from odoo.addons.horanet_subscription.controller import tools
    from odoo.addons.horanet_web.tools import route
except ImportError:
    from horanet_subscription.controller import tools
    from horanet_web.tools import route


class ServicesController(Controller):
    @http.route(['/device/horanet/unit/<int:id>', '/device/horanet/unit'], type='json', auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def WasteSite(self, device_rec, id=None, **data):
        """Return the list of waste sites."""
        result = {}
        unit_model = request.env['product.uom'].sudo()

        if id:
            result = unit_model.browse([id]).read(['write_date', 'name', 'category_id', 'display_name'])[0]
        else:
            result = unit_model.search([]).read(['write_date', 'name', 'category_id', 'display_name'])
        return result
