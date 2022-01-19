# -*- coding: utf-8 -*-
import json
import logging

import requests

from odoo import models, fields, api, exceptions, _
from ..config.config import TPA_NAME

_logger = logging.getLogger(__name__)


class TPASynchronizationMergeSmartEco(models.Model):
    """This class represent a model intended to synchronize a res.partner with a third party application."""

    # region Private attributes
    _inherit = 'tpa.synchronization.merge'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # tpa_name = fields.Selection(selection_add=[(TPA_NAME, "SmartEco")])

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.model
    def cron_action_merge_smarteco(self, options):
        """Cron method to merge SmartEco TPA periodically.

        :param options: dict(max_retry, limit) parameters for cron mechanic:
            - try_number: try limit of synchronization
            - limit: maximum records sent by request
        :return: nothing
        """
        _logger.info("Cron method cron_action_merge_SmartEco called")
        if self.env['collectivity.config.settings'].get_tpa_smarteco_is_enable():
            search_filter = []
            max_retry = int(options.get('max_retry', 10))
            search_filter.append(('try_number', '<', max_retry))
            search_filter.append(('tpa_name', '=', TPA_NAME))
            search_filter.append(('status', '=', 0))

            limit = int(options.get('limit', 10))
            recs_to_merge = self.search(search_filter, limit=limit)

            for rec_to_merge in recs_to_merge:
                if rec_to_merge:
                    _logger.info("Start items merge : " + str(rec_to_merge.ids))
                    rec_to_merge.smarteco_merge()

    # endregion

    # region Model methods
    @api.multi
    def smarteco_merge(self, context={}, **kwargs):
        """Entry point of TPA SmartEco synchronization merge service.

        :return: nothing
        """
        try:
            force = context.get('force', False)
            if force or self.env['collectivity.config.settings'].get_tpa_smarteco_is_enable():
                data = {}
                data['external_id_src'] = str(self.external_id_src)
                data['external_id_dest'] = str(self.external_id_dest)

                partner_merge = self
                url = partner_merge._smarteco_getSetting_url(self)
                data_merge = []
                data_merge.append(data)
                partners_data = dict([('merge', data_merge)])

                request = requests.post(url, json=partners_data, headers={'Content-Type': 'application/json'})

                # WARNING (because of the possible call via a thread) : make one write by self.rec
                write_result = self.get_request_write_result(request)

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
                if write_value['last_message_export'].find("Erreur :") == -1:
                    rec.status = 1
                rec.try_number = rec.try_number + 1
                rec.write(write_value)

    def get_request_write_result(self, request):
        """Get a tuple list (record, write_data) to update all models once.

        :param request: request for TPA SmartEco synchronization
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
                             for x in json.loads(request.text)['d']]
            except Exception, e:
                msg = "Bad or missing values in JSON response :" + str(e)
                # Stack trace is lost when raising a new exception, but it's not important here
                raise Exception(msg)
            else:
                # Linking responses with each of the records in the case of a multiple call
                for rec in self:
                    concerned_response = next((r for r in responses if r['ext_id'] == rec.external_id_dest), [False])
                    if len(concerned_response) == 1 and not concerned_response[0]:
                        concerned_response = next((r for r in responses if r['ext_id'] == ""), [False])
                    result.append(
                        (rec,
                         {
                             'last_message_export': unicode(concerned_response['message'])
                             if concerned_response else _("No answer from the service, the made supposed treatment."),
                             'try_number': rec.try_number + 1,
                             'last_sync_try': fields.Datetime.now(),
                             'last_sync_date': fields.Datetime.now() if concerned_response['is_sync'] else None,
                         }))
        return result

    @staticmethod
    def _smarteco_getSetting_url(self):
        """Private method to get TPA Aquagliss settings URL.

        :return: URL of TPA Aquagliss web service
        """
        backend_url = self.env['collectivity.config.settings'].get_tpa_smarteco_backend_url()
        method_name = 'mergeOdooPartner'
        if not method_name or not backend_url:
            raise exceptions.MissingError("TPA Aquagliss settings invalid (check url and method name)")
        url = backend_url + (('/' + method_name) if (method_name and method_name != 'False') else '')
        return url

    # endregion

    # endregion
    pass
