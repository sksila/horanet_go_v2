import logging
from datetime import datetime

import werkzeug.exceptions
from dateutil import parser

from odoo import http
from odoo.http import request
from . import tools

# try:
#     from odoo.addons.horanet_web.tools import route, http_exception
# except ImportError:
#     from horanet_web.tools import route, http_exception

_logger = logging.getLogger(__name__)


class OperationController(http.Controller):
    @http.route('/device/hdcom/operation/', type='http', auth="none", csrf=False)
    @tools.device_operation_standard_route
    def webservice_hdcom_operation(self, device_rec, action_rec, quantity, offline, tag_rec=None, checkpoint_rec=None,
                                   activity_sector_rec=None, activity_rec=None, **kw):
        if not checkpoint_rec:
            if len(device_rec.check_point_ids) == 1:
                checkpoint_rec = device_rec.check_point_ids[0]
        if checkpoint_rec and checkpoint_rec.activity_ids and len(checkpoint_rec.activity_ids) == 1:
            activity_rec = checkpoint_rec.activity_ids[0]
        if not activity_sector_rec and checkpoint_rec:
            activity_sector_rec = checkpoint_rec.input_activity_sector_id
        infrastructure_rec = kw.get('infrastructure_rec', False)
        if not infrastructure_rec and checkpoint_rec and checkpoint_rec.infrastructure_id:
            infrastructure_rec = checkpoint_rec.infrastructure_id

        operation = self.create_operation(device_rec, tag_rec, action_rec, quantity, offline, checkpoint_rec,
                                          activity_sector_rec, activity_rec, kw.get('time', False), infrastructure_rec)
        return {
            'status': 'ok',
            'message': 'operation ' + operation.display_name + ' created and processed'
        }

    @http.route('/device/operation/', type='json', auth="none", csrf=False)
    @tools.device_operation_standard_route
    def webservice_device_operation(self, device_rec, tag_rec, action_rec, quantity, offline, checkpoint_rec=None,
                                    activity_sector_rec=None, activity_rec=None, **post):
        operation = self.create_operation(device_rec, tag_rec, action_rec, quantity, offline, checkpoint_rec,
                                          activity_sector_rec, activity_rec, post.get('time', False),
                                          post.get('infrastructure_rec', False))
        return {
            'status': 'ok',
            'message': 'operation ' + operation.display_name + ' created and processed'
        }

    def create_operation(self, device_rec, tag_rec, action_rec, quantity, offline=False, checkpoint_rec=None,
                         activity_sector_rec=None, activity_rec=None, time=None, infrastructure_rec=None):
        # Ajout de la date avec test de conversion
        if time and isinstance(time, str):
            try:
                time = parser.parse(time)
            except ValueError:
                raise werkzeug.exceptions.BadRequest(
                    description='Invalid or unknown string for parameter "time" format')
        if time and not isinstance(time, datetime):
            raise werkzeug.exceptions.BadRequest(
                description='Parameter "time" must be a string or a date')

        operation = request.env['horanet.operation'].sudo().create({
            'quantity': quantity,
            'action_id': action_rec.id,
            'tag_id': tag_rec and tag_rec.id or False,
            'device_id': device_rec.id,
            'disable_computation': True if not tag_rec else False,
            'is_offline': offline,
            'activity_id': activity_rec and activity_rec.id or False,
            'check_point_id': checkpoint_rec and checkpoint_rec.id or False,
            'activity_sector_id': activity_sector_rec and activity_sector_rec.id or False,
            'infrastructure_id': infrastructure_rec and infrastructure_rec.id or False,
            'time': time or datetime.now(),
        })
        return operation
