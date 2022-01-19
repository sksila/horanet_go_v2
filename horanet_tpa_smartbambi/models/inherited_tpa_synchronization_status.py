# -*- coding: utf-8 -*-
import logging
import uuid

import requests
import simplejson

from odoo import models, fields, api, exceptions, _
from ..config.config import TPA_NAME

_logger = logging.getLogger(__name__)


class SynchroTPAsmartbambi(models.Model):
    """This class represent a model intended to synchronize a res.partner with a third party application."""

    # region Private attributes
    _inherit = 'tpa.synchronization.status'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    tpa_name = fields.Selection(selection_add=[(TPA_NAME, "SmartBambi")])

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.model
    def cron_action_synchronization_smartbambi(self, options):
        """Cron method to synchronize SmartBambi TPA periodically.

        :param options: dict(force, max_retry, limit) parameters for cron mechanic:
            - force: force update for every records
            - try_number: try limit of synchronization
            - limit: maximum records sent by request
        :return: nothing
        """
        _logger.info("Cron method cron_action_synchronization_smartbambi called.")
        if self.env['collectivity.config.settings'].get_tpa_smartbambi_is_enable():
            search_filter = []
            if not options.get('force', False):
                search_filter.append(('is_up_to_date', '=', False))

            max_retry = int(options.get('max_retry', 10))
            search_filter.append(('try_number', '<', max_retry))

            search_filter.append(('tpa_name', '=', TPA_NAME))

            limit = int(options.get('limit', 10))
            rec_to_update = self.search(search_filter, limit=limit)

            if rec_to_update:
                _logger.info("Start items synchronization: " + str(rec_to_update.ids))
                rec_to_update.smartbambi_synchronization()

    @api.multi
    def action_synchronization_smartbambi(self, context={}, **kwargs):
        """Launch TPA merge if TPA is enabled or synchronization forced and if synchronization list is not empty.

        :param context: context
        :param kwargs: optional: additional parameters
        :return: nothing
        """
        tpa_partners_to_sync = self.filtered(lambda x: x.ref_partner.tpa_membership_smartbambi)
        force = context.get('force', False)
        # Check if partner synchronization is needed
        if (force or self.env['collectivity.config.settings'].get_tpa_smartbambi_is_enable()) and \
                len(tpa_partners_to_sync):
            tpa_partners_to_sync.smartbambi_synchronization()

    # endregion

    # region Model methods

    @api.multi
    def smartbambi_synchronization(self):
        """Entry point of TPA SmartBambi synchronization service.

        :return: nothing
        """
        try:
            # If partners to synchronize
            url = self._smartbambi_getSetting_url()
            data_partners = self.smartbambi_get_data()

            request = requests.post(url, json=data_partners, headers={'Content-Type': 'application/json'})

            # WARNING (because of the possible call via a thread) : make one write by self.rec
            write_result = self.smartbambi_get_request_write_result(request)

        except Exception, e:
            # WARNING (because of the possible call via a thread) : make one write by self.rec
            _logger.warning('Failed to export : ' + str(e))
            for rec in self:
                rec.write({'last_message_export': unicode(e),
                           'last_sync_try': fields.Datetime.now(),
                           'try_number': rec.try_number + 1,
                           })
        else:
            # WARNING (because of the possible call via a thread) : make one write by self.rec
            for rec, write_value in write_result:
                rec.write(write_value)

            if self.env['collectivity.config.settings'].get_tpa_smartbambi_is_other_enable():
                # Send partners to other TPA if necessary
                try:
                    # If partners to synchronize
                    url_other_partner = self._smartbambi_getSettingOtherURL()
                    data_other_partners = self.smartbambi_other_partners_get_data()

                    # Error partners in other SmartBambi TPA are suppressed
                    if request.status_code == requests.codes.ok:
                        # If partners to synchronize with other TPA
                        if len(data_other_partners['partners']):
                            self._synchro_partner(request, data_other_partners)
                            request_other_partner = requests.post(url_other_partner, json=data_other_partners,
                                                                  headers={'Content-Type': 'application/json'})

                            # WARNING (because of the possible call via a thread) : make one write by self.rec
                            write_result_other_partner = self.smartbambi_get_request_write_result(request_other_partner)

                except Exception, e:
                    # WARNING (because of the possible call via a thread) : make one write by self.rec
                    _logger.warning('Failed to export : ' + str(e))
                    for rec in self:
                        rec.write({'last_message_export': unicode(e),
                                   'last_sync_try': fields.Datetime.now(),
                                   'try_number': rec.try_number,
                                   })
                else:
                    if len(data_other_partners['partners']):
                        # WARNING (because of the possible call via a thread) : make one write by self.rec
                        for rec, write_value in write_result_other_partner:
                            rec.write(write_value)

    def _synchro_partner(self, request, data_other_partners):
        for x in simplejson.loads(request.text)['d']:
            ext_id_partner = str(x['ext_id'])
            is_sync_partner = str.lower(str(x['status'])) == 'ok' or False
            if not is_sync_partner:
                for data_other in data_other_partners['partners']:
                    if str(data_other['ext_id']) == ext_id_partner:
                        data_other_partners['partners'].remove(data_other)
                        break

    def smartbambi_get_request_write_result(self, request):
        """Get a tuple list (record, write_data) to update all models once.

        :param request: request for TPA SmartBambi synchronization
        :return: values list to edit for every record
        """
        result = []
        if request.status_code != requests.codes.ok:
            for rec in self:
                result.append(
                    (rec,
                     {
                         'last_message_export': "JSON request failed :" + str(request.status_code),
                         'try_number': rec.try_number + 1,
                         'last_sync_try': fields.Datetime.now(),
                     })
                )
        else:
            try:
                responses = [{'ext_id': x['ext_id'],
                              'message': x['message'],
                              'is_sync': str.lower(str(x['status'])) == 'ok' or False}
                             for x in simplejson.loads(request.text)['d']]
            except Exception:
                try:
                    responses = [{'ext_id': x['ext_id'],
                                  'message': x['message'],
                                  'is_sync': str.lower(str(x['status'])) == 'ok' or False}
                                 for x in simplejson.loads(request.text)]

                except Exception, ex:
                    msg = _('Bad or missing values in JSON response : %s') % str(ex)
                    # Stack trace is lost when raising a new exception, mais ce n'est pas important ici
                    raise Exception(msg)
                else:
                    # Linking responses with each of the records in the case of a multiple call
                    for rec in self:
                        concerned_response = next((r for r in responses if r['ext_id'] == rec.external_id), [False])
                        if len(concerned_response) == 1 and not concerned_response[0]:
                            concerned_response = next((r for r in responses if r['ext_id'] == ""), [False])
                        number = 0 if concerned_response['message'].find('Succ') == 0 else rec.try_number + 1
                        result.append(
                            (rec,
                             {
                                 'last_message_export':
                                     unicode(concerned_response['message'])
                                     if concerned_response else
                                     _('No answer of the service, the made supposed treatment.'),
                                 'try_number': number,
                                 'last_sync_try': fields.Datetime.now(),
                                 'last_sync_date': fields.Datetime.now() if concerned_response['is_sync'] else None,
                             }))
            else:
                # Linking responses with each of the records in the case of a multiple call
                for rec in self:
                    concerned_response = next((r for r in responses if r['ext_id'] == rec.external_id), [False])
                    if len(concerned_response) == 1 and not concerned_response[0]:
                        concerned_response = next((r for r in responses if r['ext_id'] == ""), [False])
                    result.append(
                        (rec,
                         {
                             'last_message_export':
                                 unicode(concerned_response['message'])
                                 if concerned_response else _("No answer of the service, the made supposed treatment."),
                             'try_number': 0,
                             'last_sync_try': fields.Datetime.now(),
                             'last_sync_date': fields.Datetime.now() if concerned_response['is_sync'] else None,
                         }))
        return result

    def smartbambi_get_data(self):
        """Build data partner list for TPA SmartBambi.

        :return: data partner list
        """
        partners_data = []
        for rec in self:
            partners_data.append(SynchroTPAsmartbambi._smartbambi_get_data_partner(rec.ref_partner))
        if len(partners_data) != len(self):
            raise Exception("Error during data collection, number of records "
                            "to update should be the same as number of records send")
        return dict([('partners', partners_data)])

    def smartbambi_other_partners_get_data(self):
        """Build data partner list for other TPA SmartBambi.

        :return: data partner list
        """
        partners_data = []
        tpa_membership_other_smartbambi_to_sync = self.filtered(
            lambda rec: rec.ref_partner.tpa_membership_other_smartbambi)

        for partner_other in tpa_membership_other_smartbambi_to_sync:
            partners_data.append(SynchroTPAsmartbambi._smartbambi_get_data_partner(partner_other.ref_partner))

        return dict([('partners', partners_data)])

    @staticmethod
    def _smartbambi_get_data_partner(partner, recursion=True):
        """Build dictionary of data partner sent to TPA SmartBambi.

        :param partner: Record of res.partner
        :param recursion: If False, no propagation (avoid cyclic recursion)
        :return: partner data formatted for SmartBambi system
        """
        data = {}
        # Commons data for all partners
        data['ext_id'] = partner.get_or_create_tpa_external_id_rec(TPA_NAME).name
        if partner.company_type == 'residence':
            data['name'] = partner.residence_name
        elif partner.company_type == 'foyer':
            SynchroTPAsmartbambi._data_foyer(data, partner)
        else:
            # Recover partner data
            p = partner
            data['company_type'] = p['company_type']
            data['title_object'] = p.title.id and {'name': p.title.name, 'id': p.title.id}
            data['name'] = p['name'] and isinstance(p['name'], basestring) and p['name'].encode('utf8')
            data['display_name'] = p['display_name'] and isinstance(p['display_name'], basestring) and p[
                'display_name'].encode('utf8')
            data['lastname'] = p['lastname'] and isinstance(p['lastname'], basestring) and p['lastname'].encode('utf8')
            data['firstname'] = p['firstname'] and isinstance(p['firstname'], basestring) and p['firstname'].encode(
                'utf8')
            data['lastname2'] = p['lastname2'] and isinstance(p['lastname2'], basestring) and p['lastname2'].encode(
                'utf8')
            data['firstname2'] = p['firstname2'] and isinstance(p['firstname2'], basestring) and p['firstname2'].encode(
                'utf8')
            data['birthdate_date'] = p['birthdate_date']
            data['address_state'] = p['address_status']
            data['country_object'] = p.country_id.id and {'name': p.country_id.name, 'code': p.country_id.code}
            data['state_object'] = p.state_id.id and {'name': p.state_id.name, 'code': p.city_id.code}
            data['city_object'] = p.city_id.id and {'name': p.city_id.name, 'code': p.city_id.code}
            data['zip_code'] = p.zip_id.id and p.zip_id.name
            data['street_object'] = p.street_id.id and {'name': p.street_id.name, 'code': p.street_id.code}
            data['street_number'] = p.street_number_id.id and p.street_number_id.name
            data['street2'] = p.street2
            if recursion:
                data['relation_foyers'] = [
                    {'date_debut': relation.begin_date,
                     'date_fin': relation.end_date,
                     'is_valid': relation.is_valid,
                     'partner_ext_id': relation.partner_id.get_tpa_external_id(TPA_NAME),
                     'is_responsible': relation.is_responsible,
                     'foyer': SynchroTPAsmartbambi._smartbambi_get_data_partner(relation.foyer_id, recursion=False)
                     }
                    for relation in p.foyer_relation_ids]
                data['dependants'] = [SynchroTPAsmartbambi._smartbambi_get_data_partner(partner_dep, recursion=False)
                                      for partner_dep in p.dependant_ids]
                data['garants'] = [SynchroTPAsmartbambi._smartbambi_get_data_partner(partner_gar, recursion=False)
                                   for partner_gar in p.garant_ids]
            data['gender'] = p['gender']
            data['profile_object'] = {'id': '0', 'name': 'undefined'}
            for category in p.category_id:
                if data['profile_object']["name"] != 'ADULT' and data['profile_object']["name"] != 'CHILD':
                    if category.name == 'ADULTE':
                        data['profile_object'] = {'id': '1', 'name': 'ADULT'}
                    elif category.name == 'ADULT':
                        data['profile_object'] = {'id': '1', 'name': 'ADULT'}
                    elif category.name == 'ENFANT':
                        data['profile_object'] = {'id': '2', 'name': 'CHILD'}
                    elif category.name == 'CHILD':
                        data['profile_object'] = {'id': '2', 'name': 'CHILD'}
                    elif category.name == '':
                        data['profile_object'] = {'id': '99', 'name': p.category_id.id and p.category_id.name}
                    else:
                        data['profile_object'] = {'id': '0', 'name': 'undefined'}

            data['type'] = p['type']
            data['mobile'] = p['mobile']
            data['phone'] = p['phone']
            data['email'] = p['email']
            data['customer'] = p['customer']
            data['create_date'] = p['create_date']
        return data

    @staticmethod
    def _data_foyer(data, partner):
        data['name'] = partner.foyer_name
        foyer_members = partner.env['horanet.relation.foyer'].search_read(
            [('id', 'in', partner.foyer_member_ids.ids)])
        for foyer_member in foyer_members:
            # Add responsible(s) into interface cluster
            if (foyer_member['is_responsible']):
                responsable_partner = partner.env['res.partner'].search_read(
                    [('id', '=', foyer_member["partner_id"][0])])
                # Add uuid identifier on partner if necessary
                rec_ir_model_data = partner.env['ir.model.data'].search(
                    [('module', '=', TPA_NAME),
                     ('model', '=', 'res.partner'),
                     ('res_id', '=', responsable_partner[0]['id'])])
                if not rec_ir_model_data:
                    external_id = uuid.uuid1()
                    ir_model_data = partner.env['ir.model.data']
                    rec_ir_model_data = ir_model_data.create({
                        'module': TPA_NAME,
                        'model': 'res.partner',
                        'res_id': responsable_partner[0]['id'],
                        'name': external_id,
                        'noupdate': True
                    })
                responsable_partner[0]['ext_id'] = str(rec_ir_model_data['name'])
                # Create responsible
                r = responsable_partner[0]
                data_responsable = {
                    'ext_id': r['ext_id'],
                    'company_type': r['company_type'],
                    'title_object': r['title'] and {
                        'name': r['title'][1],
                        'id': r['title'][0]
                    },
                    'name': r['name'] and r['name'].encode('utf8'),
                    'display_name': r['display_name'] and r['display_name'].encode('utf8'),
                    'lastname': r['lastname'] and r['lastname'].encode('utf8'),
                    'firstname': r['firstname'] and r['firstname'].encode('utf8'),
                    'lastname2': r['lastname2'] and r['lastname2'].encode('utf8'),
                    'firstname2': r['firstname2'] and r['firstname2'].encode('utf8'),
                    'birthdate_date': r['birthdate_date'],
                    'address_state': r['address_status'],
                    'country_object': r['country_id'] and {
                        'name': r['country_id'][1] and r['country_id'][1].encode('utf8'),
                        'code': r['country_id'][0]
                    },
                    'state_object': r['state_id'] and {
                        'name': r['state_id'][1] and r['state_id'][1].encode('utf8'),
                        'code': r['state_id'][0]
                    },
                    'city_object': r['city_id'] and {
                        'name': r['city_id'][1] and r['city_id'][1].encode('utf8'),
                        'code': r['city_id'][0]
                    },
                    'zip_code': r['zip_id'] and r['zip_id'][1] and r['zip_id'][1].encode('utf8'),
                    'street_object': r['street_id'] and {
                        'name': r['street_id'][1] and r['street_id'][1].encode('utf8'),
                        'code': r['street_id'][0]
                    },
                    'street_number': r['street_number_id'] and r['street_number_id'][1] and r['street_number_id'][
                        1].encode('utf8'),
                    'street2': r['street2'] and r['street2'].encode('utf8'),
                    'gender': r['gender'],
                    'type': r['type'],
                    'mobile': r['mobile'],
                    'phone': r['phone'],
                    'email': r['email'],
                    'customer': r['customer'],
                    'create_date': r['create_date'],
                }
                categories = partner.env['res.partner.category'].search_read([('id', 'in', r['category_id'])])
                data_responsable['profile_object'] = {'id': '0', 'name': 'undefined'}
                for category in categories:
                    if data_responsable['profile_object']["name"] != 'ADULT' and \
                            data_responsable['profile_object']["name"] != 'CHILD':
                        if category['id'] and category['name'] == 'ADULTE':
                            data_responsable['profile_object'] = {'id': '1', 'name': 'ADULT'}
                        elif category['id'] and category['name'] == 'ADULT':
                            data_responsable['profile_object'] = {'id': '1', 'name': 'ADULT'}
                        elif category['id'] and category['name'] == 'ENFANT':
                            data_responsable['profile_object'] = {'id': '2', 'name': 'CHILD'}
                        elif category['id'] and category['name'] == 'CHILD':
                            data_responsable['profile_object'] = {'id': '2', 'name': 'CHILD'}
                        elif category['id'] and category['name'] != '':
                            data_responsable['profile_object'] = {'id': '99',
                                                                  'name': category['id'] and category['name']}
                        else:
                            data_responsable['profile_object'] = {'id': '0', 'name': 'undefined'}

                data_responsables = [1]
                data_responsables[0] = data_responsable
                # Add responsible to the family
                if 'responsables' not in data:
                    data['responsables'] = data_responsables
                else:
                    data['responsables'].insert(len(data['responsables']), data_responsables[0])
        return data

    def _smartbambi_getSetting_url(self):
        """Private method to get TPA SmartBambi settings URL.

        :return: URL of TPA SmartBambi web service
        """
        backend_url = self.env['collectivity.config.settings'].get_tpa_smartbambi_backend_url()
        method_name = self.env['collectivity.config.settings'].get_tpa_smartbambi_partner_method()
        if not method_name or not backend_url:
            raise exceptions.MissingError("TPA SmartBambi settings invalid (check url and method name)")
        url = backend_url + (('/' + method_name) if (method_name and method_name != 'False') else '')
        return url

    def _smartbambi_getSettingOtherURL(self):
        """Private method to get other TPA SmartBambi settings URL.

        :return: URL of other TPA SmartBambi web service
        """
        backend_url = self.env['collectivity.config.settings'].get_tpa_smartbambi_backend_other_url()
        method_name = self.env['collectivity.config.settings'].get_tpa_smartbambi_other_partner_method()
        if not method_name or not backend_url:
            raise exceptions.MissingError('Other TPA SmartBambi settings invalid (check url and method name)')
        url = backend_url + (('/' + method_name) if (method_name and method_name != 'False') else '')
        return url

    # endregion

    # endregion
    pass
