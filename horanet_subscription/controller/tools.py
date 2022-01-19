from functools import wraps

import werkzeug.exceptions

from odoo.http import request
from .custom_http_exception import DeviceNotFound, ActionNotFound, TagNotFound, CheckPointError, SectorError

try:
    from odoo.addons.horanet_web.tools import route
except ImportError:
    from horanet_web.tools import route
import logging

_logger = logging.getLogger(__name__)


def device_query_standard_route(func):
    @wraps(func)
    def wrap_args(*args, **kwargs):
        return func(*args, **kwargs)

    return route.standard_response(query_route(device_route(wrap_args)))


def device_operation_standard_route(func):
    @wraps(func)
    def wrap_args(*args, **kwargs):
        return func(*args, **kwargs)

    return route.standard_response(operation_route(device_route(wrap_args)))


def device_route(func):
    @wraps(func)
    def wrap_args(*args, **kwargs):
        if not kwargs.get('device_id', False):
            return werkzeug.exceptions.BadRequest(description="Required argument device_id is missing")

        # resolve device
        device_unique_id = kwargs.get('device_id')
        device_rec = request.env['horanet.device'].search([('unique_id', '=', device_unique_id)])
        if not device_rec:
            message = ("No device with the unique id '{unique_id}'"
                       " can be found, please check the configuration").format(unique_id=device_unique_id)
            return DeviceNotFound(description=message)
        else:
            # Mise à jour de la date de dernière tentative de communication
            device_rec.sudo().update_last_communication_time()
            kwargs.update({'device_rec': device_rec})
        return func(*args, **kwargs)

    return wrap_args


def query_route(func):
    @wraps(func)
    def wrap_args(*args, **kwargs):
        if not kwargs.get('action_code', False):
            return werkzeug.exceptions.BadRequest(description="Required argument action_id is missing")

        # resolve action
        action_code = kwargs.get('action_code')
        action_rec = request.env['horanet.action'].search([('code', '=', action_code)])
        if not action_rec:
            message = ("No action with the unique id '{unique_id}'"
                       " can be found, please check the configuration").format(unique_id=action_code)
            return ActionNotFound(description=message)
        else:
            kwargs.update({'action_rec': action_rec})

        # resolve tag (optional)
        tag_number = kwargs.get('tag')
        if not kwargs.get('tag', False):
            return werkzeug.exceptions.BadRequest(description="Required argument tag is missing")
        if tag_number:
            tag_rec = request.env['partner.contact.identification.tag'].search([('number', '=', tag_number)])
            if not tag_rec:
                return request.env['res.config.settings'].get_unknow_tag_route_response()
                # return TagNotFound()
            else:
                kwargs.update({'tag_rec': tag_rec})

        # resolve check-point (optional)
        checkpoint_code = kwargs.get('checkpoint_code', False)
        if checkpoint_code:
            checkpoint_rec = request.env['device.check.point'].search([('code', '=', checkpoint_code)])
            if not checkpoint_rec:
                return CheckPointError(description="Check point not found")
            elif kwargs.get('device_rec', False) and checkpoint_rec.device_id != kwargs['device_rec']:
                return CheckPointError(description="This check-point doesn't belong to this device")
            else:
                kwargs.update({'checkpoint_rec': checkpoint_rec})
        return func(*args, **kwargs)

    return wrap_args


def operation_route(func):  # noqa: C901 - Complexité à 18 du à la vérification de présence des arguments
    @wraps(func)
    def wrap_args(*args, **kwargs):
        """
        Check operation arguments.

        :param args:
        :param kwargs:
        :return: device_rec, tag_rec, action_rec, quantity, offline, checkpoint_rec, activity_rec
        """
        if not kwargs and request.httprequest.method == 'GET':
            # request._request_type == 'json'
            kwargs = {key: value for key, value in list(request.httprequest.args.items()) if not key.startswith('_')}
        # if not kwargs.get('tag', False):
        #     return werkzeug.exceptions.BadRequest(description="Required argument tag is missing")
        if not kwargs.get('action_code', False):
            return werkzeug.exceptions.BadRequest(description="Required argument action_code is missing")

        # resolve quantity
        quantity = kwargs.get('quantity', False)
        if quantity and isinstance(quantity, str):
            try:
                kwargs['quantity'] = float(kwargs['quantity'])
            except ValueError:
                return werkzeug.exceptions.BadRequest(description="Bad value for argument quantity")
        elif type(quantity) is bool or not isinstance(quantity, (float, int)):
            return werkzeug.exceptions.BadRequest(description="Required argument quantity is missing")

        if not isinstance(kwargs.get('offline', 'false'), bool):
            kwargs['offline'] = kwargs.get('offline', 'false').lower() in ['yes', 'true', '1']

        # resolve action
        action_code = kwargs.get('action_code')
        action_rec = request.env['horanet.action'].search([('code', '=', action_code)])
        if not action_rec:
            message = ("No action with the unique id '{unique_id}'"
                       " can be found, please check the configuration").format(unique_id=action_code)
            return ActionNotFound(description=message)
        else:
            kwargs.update({'action_rec': action_rec})

        # resolve tag
        tag_number = kwargs.get('tag')
        tag_rec = request.env['partner.contact.identification.tag'].search([('number', '=', tag_number)])
        if tag_number and not tag_rec:
            # return request.env['res.config.settings'].get_unknow_tag_route_response()
            return TagNotFound()
        if tag_rec:
            kwargs.update({'tag_rec': tag_rec})

        # resolve check-point (optional)
        checkpoint_code = kwargs.get('checkpoint_code', False)
        if checkpoint_code:
            checkpoint_rec = request.env['device.check.point'].search([('code', '=', checkpoint_code)])
            if not checkpoint_rec:
                return CheckPointError(description="Check point not found")
            elif 'device_rec' in kwargs and checkpoint_rec.device_id != kwargs['device_rec']:
                return CheckPointError(description="This check-point doesn't belong to this device")
            else:
                kwargs.update({'checkpoint_rec': checkpoint_rec})

        # resolve sector (optional)
        sector_code = kwargs.get('sector_code', False)
        if sector_code:
            activity_sector_rec = request.env['activity.sector'].search([('code', '=', sector_code)])
            if not activity_sector_rec:
                return SectorError(description="Sector not found")
            else:
                kwargs.update({'activity_sector_rec': activity_sector_rec})

        # resolve activity (optional)
        activity_code = kwargs.get('activity_code', False)
        if activity_code:
            activity_rec = request.env['horanet.activity'].search([('reference', '=', activity_code)])
            if not activity_rec:
                return CheckPointError(description="Activity not found")
            else:
                kwargs.update({'activity_rec': activity_rec})

        return func(*args, **kwargs)

    return wrap_args
