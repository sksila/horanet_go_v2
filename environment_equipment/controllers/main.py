# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request


class PickupImportDataController(http.Controller):
    @http.route('/environment/container/data/create/', type='json', auth='none', csrf=False, methods=['POST'])
    def environment_pav_data_create(self, code=None, data=None, **kw):

        request.env.uid = 1
        pickup_import_model = request.env['equipment.pickup.import']
        errors, pickup_import_data = pickup_import_model.pickup_import_pav_data_create(code=code, data=data)

        if errors:
            return {
                    'status': 'ko',
                    'message': errors
            }

        if pickup_import_data.errors:
            return {
                'status': 'ko',
                'message': pickup_import_data.errors
            }
        else:
            return {
                'status': 'ok',
                'message': _("pickup import data {} created and processed. {} operations created")
                .format(code, pickup_import_data.created_operations_count)
            }
