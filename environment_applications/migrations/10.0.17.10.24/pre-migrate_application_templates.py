# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

from odoo.tools import safe_eval

import json

logger = logging.getLogger(__name__)


def save_templates_document_settings(cr):
    logger.info('Migration of applications documents settings started.')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        icp = env['ir.config_parameter']

        data = {

            'address_proof_required': safe_eval(
                icp.get_param('environment_applications.address_proof_required', 'False')),
            'vehicle_card_required': safe_eval(
                icp.get_param('environment_applications.vehicle_card_required', 'False')),
            'identity_proof_required': safe_eval(
                icp.get_param('environment_applications.identity_proof_required', 'False')),
            'foyer_members_count_required': safe_eval(
                icp.get_param('environment_applications.foyer_members_count_required', 'False')),
            'residence_informations_required': safe_eval(
                icp.get_param('environment_applications.residence_informations_required', 'False')),
            'vehicle_card_pro_required': safe_eval(
                icp.get_param('environment_applications.vehicle_card_pro_required', 'False')),
            'letterhead_pro_required': safe_eval(
                icp.get_param('environment_applications.letterhead_pro_required', 'False')),
            'kbis_file_pro_required': safe_eval(
                icp.get_param('environment_applications.kbis_file_pro_required', 'False')),
        }

        params = icp.search_read([('key', '=', 'environment_applications.is_card_request_individual_active')],
                                 fields=['value'],
                                 limit=1)
        if params:
            data.update({'is_card_request_individual_active': safe_eval(params[0]['value'] or 'False')})

        params = icp.search_read([('key', '=', 'environment_applications.is_card_request_professional_active')],
                                 fields=['value'],
                                 limit=1)
        if params:
            data.update({'is_card_request_professional_active': safe_eval(params[0]['value'] or 'False')})

        json_data = json.dumps(data)

        with open('/tmp/data-environment-applications-before-10.0.17.10.24.json', 'w') as file:
            file.write(json_data)

    logger.info('Migration of applications documents settings ended.')


def migrate(cr, version):
    """Migrate applications to application templates.

    As we created application templates which can contain all required data for applications of type
    environment_support_request and environment_support_lost, we need to migrate old created applications of that types.
    """
    logger.info('Pre migration started: migrating environment applications.')
    if not version:
        return

    save_templates_document_settings(cr)
    logger.info('Pre migration of environment applications ended.')
