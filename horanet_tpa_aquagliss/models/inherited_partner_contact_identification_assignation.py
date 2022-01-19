# -*- coding: utf-8 -*-
import ast
import datetime
import logging

import requests
import simplejson

from odoo import models, fields, api, exceptions, _
from ..config.config import TPA_NAME

_logger = logging.getLogger(__name__)


class TPAAquaglissSynchronizationCardAssignation(models.Model):
    """Assign a tag to a partner for some duration."""

    # region Private attributes
    _inherit = 'partner.contact.identification.assignation'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        new_assignation = super(TPAAquaglissSynchronizationCardAssignation, self).create(vals)
        if self.env['collectivity.config.settings'].get_tpa_aquagliss_assignation_cards_enable():
            aquagliss_area = self.env['collectivity.config.settings'].get_tpa_aquagliss_area()
            if new_assignation.tag_id.mapping_id.area_id.name == aquagliss_area:
                synchro_card_tpa = self.env['collectivity.config.settings'].get_tpa_aquagliss_cards_is_enable()
                if synchro_card_tpa:
                    if not new_assignation.is_up_to_date:
                        rec_partner = new_assignation.reference_id
                        if rec_partner and rec_partner.tpa_membership_aquagliss:
                            new_assignation.aquagliss_synchronization_card()
        return new_assignation

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def aquagliss_synchronization_card(self):
        """Entry point of TPA Aquagliss card synchronization service.

        :return: nothing
        """
        try:
            # If partners to synchronize
            url = self._aquagliss_getSetting_url()
            data_cards = self.aquagliss_get_data_cards()

            request = requests.post(url, json=data_cards, headers={'Content-Type': 'application/json'})

            # WARNING (because of the possible call via a thread) : make one write by self.rec
            write_result = self.aquagliss_get_request_write_result(request)

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

    def _aquagliss_getSetting_url(self):
        """Private method to get TPA Aquagliss settings URL.

        :return: URL of TPA Aquagliss web service
        """
        backend_url = self.env['collectivity.config.settings'].get_tpa_aquagliss_backend_url()
        method_name = self.env['collectivity.config.settings'].get_tpa_aquagliss_name_method_card()
        if not method_name or not backend_url:
            raise exceptions.MissingError("TPA Aquagliss settings invalid (check url and method name)")
        url = backend_url + (('/' + method_name) if (method_name and method_name != 'False') else '')
        return url

    def aquagliss_get_data_cards(self):
        """Build data card list for TPA Aquagliss.

        :return: data card list
        """
        cards_data = []
        for rec in self:
            cards_data.append(self._aquagliss_get_data_card(rec))
        if len(cards_data) != len(self):
            raise Exception("Error during data collection, number of records "
                            "to update should be the same as number of records send")
        return dict([("cards", cards_data)])

    @staticmethod
    def _aquagliss_get_data_card(card_assignation):
        """Build dictionary of data card sent to TPA Aquagliss.

        :param card_assignation: Record of partner.contact.identification.assignation
        :return: card data formatted for Aquagliss system
        """
        data = {}
        data["id"] = card_assignation.id
        technology = card_assignation.tag_id.mapping_id.technology_id.name
        match_techno = ast.literal_eval(card_assignation.env['collectivity.config.settings'].
                                        get_tpa_aquagliss_technologies_card())
        data["technology"] = match_techno[technology.strip()]
        category = card_assignation.tag_id.medium_id.type_id.name if card_assignation.tag_id.medium_id else "Card"
        match_categ = ast.literal_eval(card_assignation.env['collectivity.config.settings'].
                                       get_tpa_aquagliss_categories_card())
        data["category"] = match_categ[category.strip()]
        data["partner_idExt"] = card_assignation.reference_id.get_or_create_tpa_external_id_rec(TPA_NAME).name
        data["serial_number"] = card_assignation.tag_id.number
        data["start_date"] = card_assignation['start_date']
        date_end_default = datetime.datetime(2050, 12, 31, 23, 59, 59)
        data["end_date"] = card_assignation['end_date'] if card_assignation['end_date'] else str(date_end_default)
        data["lose_card"] = "true" if card_assignation.tag_id.active else "false"
        data["serial_number_replace"] = ""
        # data['serial_number_replace'] = card_assignation.assignation_ref if card_assignation.assignation_ref else ''
        return data

    def aquagliss_get_request_write_result(self, request):
        """Get a tuple list (record, write_data) to update all models once.

        :param request: request for TPA Aquagliss synchronization
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
                responses = [{'ext_id': int(x['ext_id']),
                              'message': x['message'],
                              'is_sync': str.lower(str(x['status'])) == 'ok' or False}
                             for x in simplejson.loads(request.text)['d']]
            except Exception, e:
                msg = "Bad or missing values in JSON response :" + str(e)
                # Stack trace is lost when raising a new exception, but it's not important here
                raise Exception(msg)
            else:
                # Linking responses with each of the records in the case of a multiple call
                for rec in self:
                    concerned_response = next((r for r in responses if r['ext_id'] == rec.id), [False])
                    if len(concerned_response) == 1 and not concerned_response[0]:
                        concerned_response = next((r for r in responses if r['ext_id'] == ""), [False])
                    number = 0 if concerned_response['message'].find('Succ') == 0 else rec.try_number + 1
                    result.append(
                        (rec,
                         {
                             'last_message_export': unicode(concerned_response['message'])
                             if concerned_response else _(
                                 "No answer from the service, the made supposed treatment."),
                             'try_number': number,
                             'last_sync_try': fields.Datetime.now(),
                             'last_sync_date': fields.Datetime.now() if concerned_response['is_sync'] else None,
                         }))
        return result

    # endregion

    pass
