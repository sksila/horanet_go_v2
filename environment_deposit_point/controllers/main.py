# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request


class DepositImportDataController(http.Controller):
    @http.route('/environment/pav/data/create/', type='json', auth='none', csrf=False, methods=['POST'])
    def environment_pav_data_create(self, code=None, data=None, mapping_id=None, **kw):

        request.env.uid = 1
        deposit_import_data_model = request.env['deposit.import.data']
        errors, deposit_import_data = deposit_import_data_model.deposit_import_pav_data_create(code=code, data=data,
                                                                                               mapping_id=mapping_id)
        if errors:
            return {
                    'status': 'ko',
                    'message': errors
            }

        if deposit_import_data.errors:
            return {
                'status': 'ko',
                'message': deposit_import_data.errors.split('<br/>')
            }

        return {
            'status': 'ok',
            'message': _("Deposit import data {} created and processed. {} operations created")
            .format(code, deposit_import_data.created_operations_count)
        }
