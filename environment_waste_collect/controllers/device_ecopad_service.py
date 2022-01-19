# coding: utf-8
import json
import logging
from datetime import datetime

import dateutil.parser

from odoo import http, fields
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.osv import expression
from odoo.tools import safe_eval

try:
    from odoo.addons.horanet_subscription.controller import tools, custom_http_exception
    from odoo.addons.horanet_web.tools import route, http_exception
except ImportError:
    from horanet_subscription.controller import tools, custom_http_exception
    from horanet_web.tools import route, http_exception

    #

class DeviceWasteController(http.Controller):
    @http.route('/device/environment/parameters', type='json', auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def environment_get_config_parameters(self, device_rec, **data):
        """
        Return the config parameters for the ecopad.

        Those parameters are independent from the device, waste site or session. But only a registered device can
        call the route, hence the device_rec.

        :param device_rec: the device record
        :param data: data
        :return: the config parameters
        """
        icp_model = request.env['ir.config_parameter'].sudo()
        environment_config = request.env['horanet.environment.config']

        print_ticket_transaction = safe_eval(icp_model.get_param(
            'environment_waste_collect.print_ticket_transaction', 'False'))
        client_signature_required = safe_eval(icp_model.get_param(
            'environment_waste_collect.client_signature_required', 'False'))

        convert_access_mode_to_ecopad_value = {'always_on': '1',
                                               'always_off': '2',
                                               'configurable': '3'}
        ecopad_access_mode_configuration = convert_access_mode_to_ecopad_value.get(
            environment_config.get_ecopad_access_mode_configuration(), '3')

        return {
            'print_ticket_transaction': print_ticket_transaction,
            'client_signature_required': client_signature_required,
            'ecopad_tag_ext_reference_label': environment_config.get_tag_external_reference_label_ecopad(),
            'ecopad_access_mode_configuration': ecopad_access_mode_configuration,
            'ecopad_medium_assign_allowed': environment_config.get_ecopad_can_assign_medium()
        }

    @http.route('/device/environment/waste_site', type='json', auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def environment_get_waste_site(self, device_rec, fields=None, last_sync_date=None, **data):
        """Return the list of waste sites."""
        if fields and not isinstance(fields, list):
            return http_exception.ApplicationError("The parameter fields must be a list")

        waste_site_model = request.env['environment.waste.site'].sudo()

        domain = []

        if last_sync_date:
            domain.append(('write_date', '>', last_sync_date))
        wsites = waste_site_model.search(domain)
        if fields:
            result = wsites.read(fields=fields)
        else:
            result = []
            for waste_site in wsites:
                ws = waste_site.read(['description', 'name', 'write_date', 'display_address'])[0]
                ws.update({'activity_ids': []})
                sectors = waste_site.mapped('infrastructure_id.check_point_ids.input_activity_sector_id')

                # créer du mieux possible une liste de secteur associé aux activités
                act_sector = {}
                for s in sectors:
                    for a in s.activity_ids:
                        act_sector.update({a: s.read(['code'])[0]})

                for a, s in act_sector.items():
                    act = a.read(['reference', 'name'])[0]
                    act.update({'action': a.default_action_id and a.default_action_id.code or 'DEPOT'})
                    act.update({'unit_id': a.product_uom_id and a.product_uom_id.read(['name'])[0] or False})
                    act.update({'sector_id': s})
                    ws['activity_ids'].append(act)

                result.append(ws)
        return result

    @http.route('/device/environment/activity', type='json', auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def environment_get_activities(self, device_rec, ids=None, last_sync_date=None, **data):
        u"""
        Return the list of activities.

        On utilise la notion de default action pour distinguer les déchets du reste
        """
        result = []
        if ids and not isinstance(ids, list):
            return custom_http_exception.ApplicationError("The parameter ids must be a list of integer")

        activity_model = request.env['horanet.activity'].sudo()

        if ids:
            environment_activities = activity_model.browse(ids)
        else:
            domain = [('application_type', '=', 'environment')]

            if last_sync_date:
                domain.append(('write_date', '>', last_sync_date))
            environment_activities = activity_model.search(domain)

        for activity in environment_activities:
            act = activity.read(['description', 'reference', 'name', 'write_date', 'image'])[0]
            act.update({'action': activity.default_action_id and activity.default_action_id.code or 'DEPOT'})
            result.append(act)

        return result

    @http.route('/device/environment/devices/', type='json', auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def environment_get_devices(self, device_rec, device_type=None, **data):
        # sudo mode
        request.env.uid = 1

        ecopad = request.env['horanet.device'].search([('id', '=', device_rec.id), ('is_ecopad', '=', True)])
        if ecopad:
            session_number = ''
            if ecopad.ecopad_session_ids:
                session_number = ecopad.ecopad_session_ids[0].number

            return {
                'ecopad_id': ecopad.id,
                'session_number': session_number
            }

        result = []
        if device_type and not isinstance(device_type, list):
            return custom_http_exception.ApplicationError("The parameter ids must be a list of string")

        if 'gate' == device_type:
            pass

        waste_site_model = request.env['environment.waste.site'].sudo()
        waste_site_checkpoint = waste_site_model.search([]).mapped('infrastructure_id.check_point_ids')

        for cp in waste_site_checkpoint.filtered('ip_address'):
            cp_dic = cp.read(['name', 'ip_address', 'write_date'])[0]
            related_waste_site = waste_site_model.search([('infrastructure_id', '=', cp.infrastructure_id.id)])
            cp_dic.update({'type': 'gate',
                           'waste_site_id': related_waste_site.id})
            result.append(cp_dic)
        return result

    @route.jsonRoute(['/device/environment/partners/'], auth='none', csrf=False)
    @tools.device_route
    def environment_get_partners(self, device_rec, last_sync_date=None, **data):
        import logging
        _log = logging.getLogger(__name__)
        import json
        # sudo mode
        request.env.uid = 1

        cache_utility = request.env['horanet.environment.ecopad.cache.utility'].new()
        if not last_sync_date:

            _log.info("Accessing the local cache file")
            cached_partner_data, cache_date = cache_utility.get_partner_cached_data()

            if not cached_partner_data:
                _log.warning("No cached data found")
                return route.make_error("No cached data found", 450)

            else:
                _log.info("Cached data found")
                response_body = json.dumps(
                    {
                        'id': data.get('id', ''),
                        'result': {
                            'partners': cached_partner_data,
                            'real_last_sync_date': cache_date
                        }
                    })
                response = http.Response(
                    response=response_body,
                    status=200,
                    headers=[('Content-Type', 'application/json'), ('Content-Length', len(response_body))]
                )
                response = route.gzip_response(response, 6)
        else:
            real_last_sync_date = str(datetime.now())
            partner_data, date_data = cache_utility.get_environment_partner_data(last_sync_date)

            response = {
                'partners': partner_data,
                'real_last_sync_date': real_last_sync_date}

        return response

    def update_cached_partner_file(self):
        import json

        _log = logging.getLogger(__name__)
        id_guardian_cat = request.env.ref('environment_waste_collect.environment_category_guardian').id

        domain = [('id', '<', 1000000), ('has_active_environment_subscription', '=', True)]
        partner_model = request.env['res.partner']
        all_partners = partner_model.search(domain)

        list_data_partner = []
        _log.info("Generate partner cached data for #" + str(len(all_partners)))
        chunk_size = 100
        for partners in [all_partners[i * chunk_size:(i + 1) * chunk_size]
                         for i in range((len(all_partners) + chunk_size - 1))]:
            list_data_partner.extend([{
                'id': partner.id,
                'name': partner.name,
                'better_contact_address': partner.better_contact_address,
                'write_date': partner.write_date,
                'partner_category_ids': partner.subscription_category_ids.ids,
                'is_company': partner.is_company,
                'is_guardian': id_guardian_cat in partner.subscription_category_ids.ids
            } for partner in partners])

        json_data = json.dumps(list_data_partner)

        return json_data

    @route.jsonRoute(['/device/environment/contracts/'], auth='none', csrf=False)
    @tools.device_route
    def get_environment_contracts(self, device_id, last_sync_date=None, **kw):
        import logging
        _log = logging.getLogger(__name__)
        import json
        # sudo mode
        request.env.uid = 1

        cache_utility = request.env['horanet.environment.ecopad.cache.utility'].new()
        if not last_sync_date:

            _log.info("Accessing the local cache file")
            cached_contract_data, cache_date = cache_utility.get_contract_cached_data()

            if not cached_contract_data:
                _log.warning("No cached data found")
                return route.make_error("No cached data found", 450)

            else:
                _log.info("Cached data found")
                response_body = json.dumps(
                    {
                        'id': kw.get('id', ''),
                        'result': {
                            'contracts': cached_contract_data,
                            'real_last_sync_date': cache_date
                        }
                    })
                response = http.Response(
                    response=response_body,
                    status=200,
                    headers=[('Content-Type', 'application/json'), ('Content-Length', len(response_body))]
                )
                response = route.gzip_response(response, 6)
        else:
            real_last_sync_date = str(datetime.now())
            package_data, date_data = cache_utility.get_environment_package_data(last_sync_date)

            response = {
                'contracts': package_data,
                'real_last_sync_date': real_last_sync_date}

        return response

    @http.route(['/device/environment/tags/'], type='json', auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def api_v0_get_environment_tags(self, device_rec, last_sync_date=None, **data):
        """
        Get all environment tags.

        :param device_rec: the device
        :param last_sync_date: date of last synchronisation
        :param data: data
        :return: list of all environment tags
        """
        # sudo mode
        request.env.uid = 1
        if last_sync_date:
            last_sync_date = dateutil.parser.parse(last_sync_date).replace(tzinfo=None)
        return self.get_environment_tags(request.env, last_sync_date)

    @http.route(['/api/v2/device/environment/tags/'], type='json', auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def api_v2_get_environment_tags(self, device_rec, last_sync_date=None, **data):
        """
        Get all environment tags.

        :param device_rec: the device
        :param last_sync_date: date of last synchronisation
        :param data: data
        :return: list of all environment tags
        """
        # sudo mode
        request.env.uid = 1
        real_last_sync_date = str(datetime.now())
        if last_sync_date:
            last_sync_date = dateutil.parser.parse(last_sync_date).replace(tzinfo=None)

        tags_list = self.get_environment_tags(request.env, last_sync_date)
        result = {
            'tags': tags_list,
            'real_last_sync_date': real_last_sync_date
        }
        return result

    @route.jsonRoute([
        '/api/v3/device/environment/tags',
        '/api/v3/device/environment/tags/<any(help,):help>'],
        methods=['GET'], auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def api_v3_get_environment_tags(self, last_sync_date=None, partner_id=None, is_guardian=False, **data):
        u"""Get all environment tags. Using caching data if possible.

        Voir https://www.restapitutorial.com/lessons/httpmethods.html pour les bonnes pratiques

        JSON request content example:

        -  Pour récupérer les informations de tags:
            URL: GET {{odoo_url}}/api/v3/device/environment/tags?device_id={{device_id}}

            Paramètres de filtre optionnels:
                -  partner_id (int)
                -  is_guardian (boolean) -> pas de cache dans le cas des gardiens
                -  last_sync_date (exemple : last_sync_date="2018-08-23 14:55:31")

        Seulement dans le cas ou last_sync_date n'est pas fourni, le cache sera utilisé !

        - exemple de retour :

        "result": {
            "real_last_sync_date": "2018-10-17 13:45:18",
            "tags": [
                {
                    "external_reference": "",
                    "number": "99F04F040000",
                    "active": true,
                    "partner_id": false,
                    "id": 1323
                }, {...}
            ]
        }

        :param is_guardian: optional, is true, only guardian's tag are returned, si False ou non defined no
        guardian tags are returned
        :param partner_id: optional, partner used to filter tags
        :type int
        :param last_sync_date: date of last synchronisation
        :type str
        :param data: request parameters
        :return: list of all environment tags (json)
        """
        _log = logging.getLogger(__name__)
        # Affichage de la docstring (si demande d'aide)
        if 'help' in data:
            return http.Response(self.api_v3_get_environment_tags.__doc__)

        # sudo mode
        request.env.uid = 1

        if last_sync_date:
            last_sync_date = dateutil.parser.parse(last_sync_date).replace(tzinfo=None)

        cache_utility = request.env['horanet.environment.ecopad.cache.utility'].new()
        is_guardian = is_guardian and (isinstance(is_guardian, basestring) and is_guardian not in ('False', 'false'))

        if is_guardian:
            tag_data, search_date = cache_utility.get_environment_tag_data(last_sync_date or None, only_guardian=True)
            response = {
                'tags': tag_data,
                'real_last_sync_date': search_date,
                'is_guardian': True}

        elif partner_id:
            tag_data, search_date = cache_utility.get_environment_tag_data(last_sync_date or None, partner_id)
            response = {
                'tags': tag_data,
                'real_last_sync_date': search_date,
                'is_guardian': False}

        elif not last_sync_date:
            _log.info("Accessing the local cache file")
            cached_tag_data, cache_date = cache_utility.get_tag_cached_data()

            if not cached_tag_data:
                _log.warning("No cached data found")
                return route.make_error("No cached data found", 450)

            else:
                response_body = json.dumps(
                    {
                        'id': data.get('id', ''),
                        'result': {
                            'tags': cached_tag_data,
                            'real_last_sync_date': cache_date,
                            'is_guardian': False
                        }
                    })
                response = http.Response(
                    response=response_body,
                    status=200,
                    headers=[('Content-Type', 'application/json'), ('Content-Length', len(response_body))]
                )
                response = route.gzip_response(response, 6)
        else:
            tag_data, search_date = cache_utility.get_environment_tag_data(last_sync_date)
            response = {
                'tags': tag_data,
                'real_last_sync_date': search_date,
                'is_guardian': False}

        return response

    @staticmethod
    def get_environment_tags(odoo_environment, last_sync_date=None):
        """Return for the Ecopad API all the tag assigned to a partner having an environment contract (active).

        :param odoo_environment: An odoo environment
        :param last_sync_date: limit the search to the assignations write_date > last_sync_date
        :return: list of dict({
            'id': Int
            'active': Boolean
            'number': String
            'external_reference': String
            'write_date': String
            'partner_id': Int
            'is_guardian': Boolean
        """
        partner_model = odoo_environment['res.partner']
        partners = partner_model.search([('has_active_environment_subscription', '=', True)])
        assignation_model = odoo_environment['partner.contact.identification.assignation']

        search_domain = []

        if last_sync_date:
            search_domain = expression.OR([
                [('write_date', '>', fields.Datetime.to_string(last_sync_date))],
                # Rechercher aussi les assignations qui ne seraient plus actives depuis la dernière synchro
                expression.AND([
                    assignation_model.search_is_active(operator='=', value=True, search_date=last_sync_date),
                    assignation_model.search_is_active(operator='=', value=False, search_date=fields.Datetime.now())
                ]),
                # Rechercher aussi les assignations qui ne seraient devenues actives depuis la dernière synchro
                expression.AND([
                    assignation_model.search_is_active(operator='=', value=False, search_date=last_sync_date),
                    assignation_model.search_is_active(operator='=', value=True, search_date=fields.Datetime.now())
                ])
            ])

        search_partner_tag_domain = [
            '&',
            '&',
            ('reference_id', '!=', False),
            ('reference_id', '=like', 'res.partner%'),
            ('partner_id', 'in', partners.ids)
        ]

        assignations = assignation_model.search(search_partner_tag_domain + search_domain)

        id_guardian_cate = odoo_environment.ref('environment_waste_collect.environment_category_guardian').id
        return [{
            'id': assignation.tag_id.id,
            'active': assignation.tag_id.active and assignation.is_active,
            'number': assignation.tag_id.number,
            'external_reference': assignation.tag_id.external_reference,
            'write_date': assignation.write_date,
            'partner_id': assignation.reference_id.id,
            'is_guardian': id_guardian_cate in assignation.reference_id.subscription_category_ids.ids
        } for assignation in assignations]

    @http.route(['/device/environment/ecopad/sessions/'], type='json', auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def environment_ecopad_session(self, device_rec, session_ids, **data):
        session_model = request.env['environment.ecopad.session'].sudo()
        activity_sectors_ids = request.env['activity.sector'].sudo().search([
            ('activity_ids.application_type', '=', 'environment')])
        nb_session_closed = 0
        nb_session_created = 0
        nb_session_ignored = 0

        for session in session_ids:
            session_rec = session_model.search([
                ('number', '=', session.get('number')), ('ecopad_id', '=', device_rec.id)])

            # Close session if already exists and end_date is set.
            if session_rec:
                if session.get('end_date'):
                    if session_rec.end_date_time:
                        nb_session_ignored += 1
                    else:
                        session_rec.write({
                            'end_date_time': session.get('end_date'),
                            'nb_transactions_from_ecopad': session.get('nb_transactions'),
                            'nb_operations_from_ecopad': session.get('nb_operations')
                        })
                        nb_session_closed += 1
                else:
                    nb_session_ignored += 1
            elif not session_rec:
                session_model.create({
                    'guardian_id': int(session['user_id']),
                    'start_date_time': session['begin_date'],
                    'end_date_time': session.get('end_date', None),
                    'tag_id': int(session['tag']['id']),
                    'ecopad_id': device_rec.id,
                    'waste_site_id': int(session['waste_site_id']),
                    'activity_sector_ids': activity_sectors_ids.ids,  # useless for now
                    'number': session.get('number'),
                    'last_number': session.get('last_session_number', False),
                    'nb_transactions_from_ecopad': session.get('nb_transactions'),
                    'nb_operations_from_ecopad': session.get('nb_operations')
                })
                nb_session_created += 1

        return {
            'nb_session_closed': nb_session_closed,
            'nb_session_ignored': nb_session_ignored,
            'nb_session_created': nb_session_created
        }

    @http.route('/device/environment/ecopad/operation/', type='json', auth='none', csrf=False)
    @tools.device_operation_standard_route
    def environment_ecopad_operation(self, device_rec, tag_rec, action_rec, quantity, offline, number,
                                     checkpoint_rec=None, activity_sector_rec=None, activity_rec=None,
                                     time=None, **kw):
        # sudo mode
        request.env.uid = 1

        operation = False
        operation_model = request.env['horanet.operation']

        session_rec, transaction_number, transaction_rec = self.get_session_and_transaction(number, device_rec)

        if not session_rec:
            return route.make_error("Session not found", 400)

        operation_ids = transaction_rec.operation_ids.filtered(lambda a: a.number == number)
        if len(operation_ids) > 1:
            return route.make_error("Error to many operation existing in this transaction with this number", 400)

        # 3 - Create the operation
        if not operation_ids:
            # Ecopad does not send the activity action code when it's an access
            if activity_sector_rec and not activity_rec:
                activity_passage_ids = activity_sector_rec.activity_ids.filtered(
                    lambda a: a.default_action_id.code == kw.get('action_code'))
                activity_rec = activity_passage_ids and activity_passage_ids[0] or False

            operation = operation_model.create({
                'quantity': quantity,
                'action_id': action_rec.id,
                'tag_id': tag_rec.id,
                'device_id': device_rec.id,
                'activity_id': activity_rec.id,
                'check_point_id': checkpoint_rec and checkpoint_rec.id or False,
                'activity_sector_id': activity_sector_rec and activity_sector_rec.id or False,
                'number': number,
                'ecopad_transaction_id': transaction_rec.id,
                'infrastructure_id': session_rec.waste_site_id.infrastructure_id.id,
                'is_offline': False,
                'time': time or datetime.now(),
            })

        return {
            'status': 'ok',
            'message': 'operation ' + str(operation and operation.display_name or False) + ' created and processed'
        }

    @http.route('/device/environment/ecopad/operation/signature', type='json', auth='none', csrf=False)
    @route.standard_response
    @tools.device_route
    def environment_ecopad_operation_signature(self, device_rec, number, signature, **kw):
        u"""
        Cette route est appelée pour uploader la signature d'un panier.

        :param device_rec: l'ecopad
        :param signature: la signature en base64
        :param number: le numéro de la transaction
        :param kw: kw
        :return: un message de succès
        """
        # sudo mode
        request.env.uid = 1

        session_rec, transaction_number, transaction_rec = self.get_session_and_transaction(number, device_rec)

        if not session_rec:
            return route.make_error("Session not found", 400)

        transaction_rec.ecopad_signature = signature

        return {
            'status': 'ok',
            'message': 'transaction ' + str(transaction_rec) + ' signature processed'
        }

    @route.jsonRoute('/device/environment/wastesite/<int:waste_site_id>/fmi', auth='none', csrf=False)
    @tools.device_route
    def webservice_wastesite_FMI(self, device_rec, waste_site_id, disable=None, enable=None, calibrate=None, **post):
        u"""Webservice de gestion de la FMI des déchetteries.

        :param device_rec: Communicating device
        :param waste_site_id: The waste site on which the FMI will be set
        :param disable: If True - disable the FMI control on this wastesite for the day
        :param enable: If True - enable the FMI control on this wastesite for the day
        :param calibrate: Use with quantity, set at the request time th FMI value
        """
        waste_site_rec = request.env['environment.waste.site'].sudo().browse(waste_site_id)
        if not waste_site_id:
            return route.make_error('Waste site with id ' + str(waste_site_id) + ' not found', 400)
        else:
            pass
        if request.httprequest.method == 'GET':
            return {
                'has_fmi': waste_site_rec.is_attendance_controlled or False,
                'current_attendance': waste_site_rec.get_current_attendance(),
                'is_fmi_control_enable': waste_site_rec.is_fmi_control_enable(),
                'attendance_threshold': waste_site_rec.attendance_threshold,
                'can_attend': waste_site_rec.can_attend()
            }
        elif request.httprequest.method == 'POST':
            if disable and enable:
                return route.make_error('Should I disable or enable the FMI !?', 400)
            if calibrate and (disable or enable):
                return route.make_error('This service only calibrate OR enable/disable the FMI', 400)

            operation_model = request.env['horanet.operation'].sudo()
            tag_rec = False
            if 'tag_number' in post:
                tag_number = post.get('tag_number')
                tag_rec = request.env['partner.contact.identification.tag'].sudo().search(
                    [('number', '=', tag_number)])
                if not tag_rec:
                    return custom_http_exception.TagNotFound()
            vals = {
                'action_id': request.env.ref('horanet_subscription.action_calibrate_fmi').id,
                'tag_id': tag_rec and tag_rec.id or None,
                'device_id': device_rec.id,
                'disable_computation': True,
                'number': post.get('id', None),
                'infrastructure_id': waste_site_rec.infrastructure_id.id,
                'is_offline': False,
            }
            # Ajout de la date avec test de conversion
            if post.get('time', False):
                try:
                    time = dateutil.parser.parse(post['time'])
                    vals.update({'time': time})
                except ValueError:
                    return route.make_error('Invalid or unknown string for parameter "time" format', 400)

            operation = None
            if calibrate:
                vals.update({'action_id': request.env.ref('horanet_subscription.action_calibrate_fmi').id,
                             'quantity': int(calibrate)})
                operation = operation_model.create(vals)
            elif disable:
                vals.update({'action_id': request.env.ref('horanet_subscription.action_disable_fmi').id})
                operation = operation_model.create(vals)
            elif enable:
                vals.update({'action_id': request.env.ref('horanet_subscription.action_enable_fmi').id})
                operation = operation_model.create(vals)

            if operation:
                return {'message': 'operation created'}
            else:
                return {'message': 'Nothing to do, nothing done !'}
        else:
            return route.make_error('Only POST and GET methods are defined for this service', 400)

    @route.jsonRoute('/device/environment/prices/', auth='none', csrf_token=False)
    @tools.device_route
    def get_environment_prices(self, device_id, last_sync_date=None, **kw):
        """
        Get prices for environment activities.

        :param device_id: the id of the device
        :param last_sync_date: the last synchronisation date
        :return: list fo prices
        """
        # sudo mode
        request.env.uid = 1

        activity_model = request.env['horanet.activity']

        activities = activity_model.search([
            ('application_type', '=', 'environment'),
            ('product_id.item_ids', '!=', False)
        ])
        pricelist_items = activities.mapped('product_id.item_ids')

        if last_sync_date:
            pricelist_items.filtered(lambda p: p.write_date > last_sync_date)
            activities.filtered(lambda a: a.product_id in pricelist_items.mapped('product_id'))

        prices = []
        for activity in activities:
            product_template = activity.product_id.product_tmpl_id
            for pricelist_item in pricelist_items.filtered(lambda p: p.product_tmpl_id == product_template):
                prices.append({
                    'id': pricelist_item.id,
                    'price': pricelist_item.fixed_price,
                    'start_date': pricelist_item.date_start,
                    'end_date': pricelist_item.date_end,
                    'activity_id': activity.id,
                    'currency': request.env.user.company_id.currency_id.name,
                    'partner_category_ids': pricelist_item.partner_category_ids.ids,
                    'unit': activity.product_uom_id.with_context(lang='fr_FR').read(['name'])[0]
                })

        return prices

    @route.jsonRoute('/device/environment/partner_categories/', auth='none', csrf_token=False)
    @tools.device_route
    def get_environment_partner_categories(self, device_id, last_sync_date=None, **kw):
        """
        Get the list of all partner categories.

        :param device_id: the id of the device
        :param last_sync_date: the last synchronisation date
        :return: the list of all partner categories
        """
        # sudo mode
        request.env.uid = 1

        partner_category_model = request.env['subscription.category.partner']

        return partner_category_model.search_read([
            ('application_type', '=', 'environment')
        ], ['id', 'name'])

    @route.jsonRoute(['/device/environment/medium-assign/'], auth='none', csrf=False)
    @tools.device_route
    def ecopad_assign_medium(self, device_rec, partner, number, tech_codes, last_sync_date=None, **data):
        """
        Assign a new medium.

        :param device_rec: the device
        :param partner: the partner to assign the medium to
        :param number: the number of the medium
        :param tech_codes: list of technology codes for the mapping
        :param last_sync_date: the last synchronisation date
        :return: the new assignation or error
        """
        # sudo mode
        request.env.uid = 1
        mapping_env = request.env['partner.contact.identification.mapping']

        # On va chercher si on peut assigner un tag depuis l'ecopad
        can_assign_medium = request.env['horanet.environment.config'].get_ecopad_can_assign_medium()
        if not can_assign_medium:
            return route.make_error("Can't assign medium: the option is deactivated", 447)

        # On va chercher le mapping par défaut
        default_mapping_id = safe_eval(request.env['ir.config_parameter'].get_param(
            'partner_contact_identification.default_mapping_id', 'False'
        ))
        default_mapping_id = mapping_env.search([('id', '=', default_mapping_id)])
        # Le partner
        partner = request.env['res.partner'].search([('id', '=', int(partner))])

        # Pour le mapping, celui-ci dépend de la technologie et on le prend toujours en CSN
        mappings = mapping_env.search([('technology_id.code', 'in', tech_codes), ('mapping', '=', 'csn')])
        if mappings:
            mapping = mappings[0]
        else:
            mapping = default_mapping_id

        if mapping and partner:
            tag_model = request.env['partner.contact.identification.tag']
            try:
                tag = tag_model.create({
                    'number': number,
                    'mapping_id': default_mapping_id.id
                })
                request.env['partner.contact.identification.wizard.create.medium'].create_assignation(tag.id,
                                                                                                      'res.partner',
                                                                                                      partner.id)
                request.env['partner.contact.identification.wizard.create.medium'].create_medium([tag.id], False)
            except ValidationError as e:
                return route.make_error(e.name, 446)
        elif not mapping:
            return route.make_error("Can't assign medium: there is no default mapping defined", 447)
        elif not partner:
            return route.make_error("Can't assign medium: partner not found", 446)

        # On va chercher la nouvelle assignation
        assignation_model = request.env['partner.contact.identification.assignation']
        assignation = assignation_model.search([('partner_id', '=', partner.id), ('tag_id', '=', tag.id)])

        return [{
            'id': assignation.tag_id.id,
            'active': assignation.tag_id.active,
            'number': assignation.tag_id.number,
            'external_reference': assignation.tag_id.external_reference,
            'write_date': assignation.write_date,
            'partner_id': assignation.reference_id.id,
            'is_guardian':
                request.env.ref('environment_waste_collect.environment_category_guardian').id
                in assignation.reference_id.subscription_category_ids.ids
        }]

    def get_session_and_transaction(self, number, device_rec):
        """Get session and transaction informations.

        :param number: session number
        :param device_rec: the device record
        :return: session record, transaction number and transaction record
        """
        # 1 - Get session
        session_number = number.split('-')[0]
        session_rec = request.env['environment.ecopad.session'].sudo().search([
            ('number', '=', session_number),
            ('ecopad_id', '=', device_rec.id)])
        if not session_rec:
            return

        # 2 - Get or create transaction
        transaction_number = session_number + number.split('-')[1]
        transaction_model = request.env['environment.ecopad.transaction'].sudo()
        transaction_rec = transaction_model.search([
            ('number', '=', transaction_number),
            ('ecopad_session_id', '=', session_rec.id)])

        if not transaction_rec:
            transaction_rec = transaction_model.create({
                'number': transaction_number,
                'ecopad_session_id': session_rec.id})

        return session_rec, transaction_number, transaction_rec

    @route.jsonRoute('/device/environment/rule/query', auth='none', csrf=False)  # noqa: C901
    @tools.device_route
    def device_environment_rule_query(self, device_rec, tag_number=None, debug=False,
                                      partner_id=None, activity_ids=None, action_code=None, wastesite_id=None, **kw):
        # sudo mode
        request.env.uid = 1
        action_rec = False
        partner_rec = False
        waste_site_rec = False
        activities_rec = False
        # _logger = logging.getLogger('/device/environment/rule/query')
        try:
            from odoo.addons.horanet_subscription.models.exploitation_engine import exploitation_engine as hora_engine
        except ImportError:
            from horanet_subscription.models.exploitation_engine import exploitation_engine as hora_engine
        current_time = datetime.now()

        # region 1 - test parameters
        # resolve activities
        if not activity_ids:
            return route.make_error("Argument 'activity_ids' is mandatory", 400)
        if activity_ids and not isinstance(activity_ids, list):
            return route.make_error(
                "Argument 'activity_ids' should be a list of integer, got {bad_type} instead".format(
                    bad_type=str(type(activity_ids))), 400)
        if not all(isinstance(activity_id, int) for activity_id in activity_ids):
            return route.make_error(
                "Argument 'activity_ids' should be a list of integer, items in the list are not integers", 400)
        activities_rec = request.env['horanet.activity'].search([('id', 'in', activity_ids)])
        if len(activity_ids) > len(activities_rec):
            return route.make_error(
                "Some activities id couldn't be found. ID(s) ('{not_found_ids}') do not exist.".format(
                    not_found_ids=', '.join([str(a_id) for a_id in activity_ids if a_id not in activities_rec.ids])),
                446)
        # resolve action code
        if action_code and not isinstance(action_code, str):
            return route.make_error(
                "Argument 'action_code' should be a string, got {bad_type} instead".format(
                    bad_type=str(type(action_code))), 400)
        if action_code:
            action_rec = request.env['horanet.action'].search([('code', '=', action_code)])
            if not action_rec:
                return route.make_error(
                    "Action not found. The action code '{action_code}' does not exist".format(
                        action_code=str(action_code)), 442)
        # resolve wastes site id
        if not wastesite_id:
            return route.make_error("Argument 'wastesite_id' is mandatory", 400)
        if wastesite_id and not isinstance(wastesite_id, int):
            return route.make_error(
                "Argument 'infrastructure_id' should be an integer, got {bad_type} instead".format(
                    bad_type=str(type(wastesite_id))), 400)
        if wastesite_id:
            waste_site_rec = request.env['environment.waste.site'].search([('id', '=', wastesite_id)])
            if not waste_site_rec:
                return route.make_error(
                    "Wastesite not found. The wastesite id '{wastesite_id}' does not exist".format(
                        wastesite_id=str(wastesite_id)), 442)

        # resolve partner id and tag_number
        if partner_id and tag_number:
            return route.make_error(
                "Only one of the parameters 'tag_number' and 'partner_id' should be set", 400)
        if not partner_id and not tag_number:
            return route.make_error(
                "One of the parameters 'tag_number' or 'partner_id' should be set", 400)
        if tag_number:
            if not isinstance(tag_number, str):
                return route.make_error(
                    "Argument 'tag_number' should be an string, got {bad_type} instead".format(
                        bad_type=str(type(tag_number))), 400)
            else:
                tag_rec = request.env['partner.contact.identification.tag'].search([('number', '=', tag_number)])
                if not tag_rec:
                    return route.make_error(
                        "Tag not found. The tag number '{tag_number}' does not exist".format(
                            tag_number=str(tag_number)), 444)
                partner_rec = tag_rec.partner_id
                if not partner_rec:
                    return route.make_error(
                        "No partner found with the tag number '{tag_number}'.".format(
                            tag_number=str(tag_number)), 445)
        if partner_id:
            if not isinstance(partner_id, int):
                return route.make_error(
                    "Argument 'partner_id' should be an int, got {bad_type} instead".format(
                        bad_type=str(type(partner_id))), 400)
            partner_rec = request.env['res.partner'].search([('id', '=', partner_id)])
            if not partner_rec:
                return route.make_error(
                    "Partner not found. The partner id '{partner_id}' does not exist".format(
                        partner_id=str(partner_id)), 443)
        # endregion

        # region 2 - find best sector
        activity_sectors = request.env['device.check.point'].search(
            [('infrastructure_id', '=', waste_site_rec.infrastructure_id.id)]).mapped('input_activity_sector_id')

        rule_model = request.env['activity.rule']
        list_rules_to_execute = request.env['activity.rule']
        for sector in activity_sectors:
            rules_to_execute = rule_model.resolve_rule_execution_plan(activities_rec, action=action_rec, sector=sector)
            list_rules_to_execute += rules_to_execute
        list_rules_to_execute = list_rules_to_execute & list_rules_to_execute

        # Recherche d'une action par défaut si pas d'action fournie
        if not action_rec:
            default_action = activities_rec.mapped('default_action_id')
            action_rec = default_action[0] if default_action else action_rec

        dummy_query = request.env['device.query'].new({
            'action_id': action_rec and action_rec,
            'partner_id': partner_rec,
            'device_id': device_rec,
            'time': current_time,
        })
        exploitation_engine = request.env['exploitation.engine'].sudo().new({'trigger': dummy_query})
        # Hack to force value in cache for new record
        exploitation_engine.trigger_query.partner_id = partner_rec

        activities, packages, log = exploitation_engine._resolve_trigger_activity(current_time)
        list_execution_results = []
        for rule in list_rules_to_execute:
            instance_rule_execution, exec_status, exec_log = exploitation_engine.execute_rule_with_log(
                rule=rule, activity=False, trigger=dummy_query, package_ids=packages, force_time=current_time)

            list_execution_results.append({'status': exec_status,
                                           'instance': instance_rule_execution,
                                           'rule': rule,
                                           'log': exec_log})

        rules_result = []
        for execution_result in list_execution_results:
            if execution_result['status'] not in [hora_engine.EXECUTION_ERROR, hora_engine.EXECUTION_EMPTY]:
                # Si pas error ou empty, une query aura une réponse (unique)
                response = execution_result['instance'].execution_result['responses'][0]
                rule_result = {
                    'message': response['message'] or '',
                    'activity_ids': execution_result['rule'].activity_ids.ids,
                    'result': response['response'],
                    'name': execution_result['rule'].name,
                }
                if debug:
                    rule_result['log'] = execution_result['log']

                rules_result.append(rule_result)

        response = {'rules': rules_result}
        if debug:
            response['log_debug'] = log

        return response

    @route.jsonRoute(['/api/device/informations/'], auth='none', csrf=False)
    @tools.device_route
    def api_device_set_informations(self, device_rec, **kw):
        u"""Méthode de renseignement d'informations (diverses) d'un horanet.device.

        Cette méthode permet de renseigner le champ device_detail d'un device. Cela permet par exemple à un
        Ecopad de fournir au back-office les informations de versions de l'application, ou quoi que ce soit d'autre.

        Exemple d'utilisation (json body):
            {
               "informations":{
                    "IMEI":"358599060137895, 358599080137903",
                    "Fleet":"Client ABCDE",
                    "Profile":"Ecopad 2.1.1 (from fleet)",
                    "Applications":"Chrome 46.0.2490.76",
                    "Autolaunch application":"-",
                    "NFC":"On",
                    "WiFi":"On",
                    "Developer mode":"On",
                    "OS version":"FX200,2_v0.10.0_20170517",
                    "Synchronization interval":"1 Hour",
                    "Last synchronization date":"Sep 29, 2017, 10:43",
                    "Synchronization status":"Not synced",
                    "Maintenance status":"In the field",
                    "Heartbeat":"Alert",
                    "System Applications":"com.famoco.settings 1152",
                    "com.famoco.launcher":"1114",
                    "com.famoco.fms":"2232",
                    "time":"2017-09-15 08:35:40"
               },
               "device_id":"1231354645",
               "id": {{$randomInt}}
            }

        :param device_rec:
        :param kw: Le contenu Json devant contenir un dictionnaire 'informations'
        :return: True or Exception
        """
        if 'informations' in kw:
            device_information = kw.get('informations', '---')
            device_rec.sudo().device_detail = json.dumps(device_information, indent=2, sort_keys=True)

        else:
            return route.make_error("No informations data found", 400)

        return True
