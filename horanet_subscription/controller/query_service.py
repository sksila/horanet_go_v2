import logging

from odoo import http
from odoo.http import request
from . import tools

# try:
#     from odoo.addons.horanet_web.tools import route, http_exception
# except ImportError:
#     from horanet_web.tools import route, http_exception

_logger = logging.getLogger(__name__)


class HoranetWebsiteController(http.Controller):
    @http.route('/device/query/', type='http', auth="none", csrf=False)
    @tools.device_query_standard_route
    def HDCOMServiceQuery(self, action_rec, device_rec, tag_rec=None, checkpoint_rec=None, **kw):
        """Service de recherche des traductions des modules dépendants de horanet_website.

        Ce controller est appelé par le JS pour valuer le dictionnaire des traductions (voir fonction js _t())
        :param lang: Le code de la langue à traduire
        :return: un objet json contenant la liste des clés/valeur de chaînes traduite par module
        """
        response_rec = None
        query = None
        engine_result = None
        if not checkpoint_rec:
            if len(device_rec.check_point_ids) == 1:
                checkpoint_rec = device_rec.check_point_ids[0]
        try:
            query = request.env['device.query'].sudo().create({
                'action_id': action_rec.id,
                'tag_id': tag_rec and tag_rec.id or False,
                'device_id': device_rec.id,
                'check_point_id': checkpoint_rec and checkpoint_rec.id or False,
            })

            exploitation_engine = request.env['exploitation.engine'].sudo().new({'trigger': query})
            engine_result = exploitation_engine.compute(simulation=False)

            # responses, operations, usages, log, activity, usage_recs, exception = request.env[
            #     'activity.rule.wizard.sandbox'].sudo().engine_execution_with_log(query)
            #
            # if responses and len(responses) == 1:
            #     response_rec = request.env['device.response'].sudo().create({
            #         'query_id': query.id,
            #         'response': responses[0]['response'],
            #         'message': responses[0].get('message', ''),
            #         'rule_log': log,
            #     })
            #     if operations:
            #         operation_model = request.env['horanet.operation'].sudo()
            #         activity_rec = False
            #         if activity and len(activity) == 1:
            #             activity_rec = activity
            #         for operation in operations:
            #             new_operation = operation_model.operation_from_rule_query(
            #                 query, operation, activity_id=activity_rec, log=log)
            response_rec = engine_result and engine_result.response_id and engine_result.response_id[0]
        except Exception as e:
            # if query and log:
            #     query.rule_log = log
            _logger.warning("Unexpected exception : " + str(e))
            raise

        # if query and log:
        #     query.rule_log = log

        return {
            'response': response_rec.response,
            'message': response_rec.message or "Check log, impossible to get a response",
        }
