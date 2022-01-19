# coding: utf-8

import logging

from psycopg2 import ProgrammingError

from odoo import api, SUPERUSER_ID

import json

logger = logging.getLogger(__name__)


def update_templates_document_settings(cr):
    logger.info('Migration of applications documents settings started.')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        config_before = {}
        with open('/tmp/data-environment-applications-before-10.0.17.10.24.json') as json_data:
            config_before = json.load(json_data)

        # Mise à jour des templates en fonction des anciennes configurations
        if 'is_card_request_professional_active' not in config_before or config_before[
           'is_card_request_professional_active']:
            attachment_types = env['ir.attachment.type']
            template = env.ref('environment_applications.application_template_support_request_pro')
            if config_before.get('letterhead_pro_required', False):
                attachment_types += env.ref('environment_applications.attachment_type_letterhead')
            if config_before.get('kbis_file_pro_required', False):
                attachment_types += env.ref('environment_applications.attachment_type_kbis_file')
            if config_before.get('vehicle_card_pro_required', False):
                attachment_types += env.ref('environment_applications.attachment_type_vehicle_registration_card')
            template.attachment_types = attachment_types

        if 'is_card_request_individual_active' not in config_before or config_before[
           'is_card_request_individual_active']:
            attachment_types = env['ir.attachment.type']
            template = env.ref('environment_applications.application_template_support_request_part')
            if config_before.get('identity_proof_required', False):
                attachment_types += env.ref('environment_applications.attachment_type_proof_of_identity')
            if config_before.get('address_proof_required', False):
                attachment_types += env.ref('partner_documents.attachment_type_proof_of_address')
            if config_before.get('vehicle_card_required', False):
                attachment_types += env.ref('environment_applications.attachment_type_vehicle_registration_card')
                template.attachment_types = attachment_types

    logger.info('Migration of applications documents settings ended.')


def update_applications_informations(cr):
    logger.info('Migration of applications informations started.')

    try:

        if get_field_exists(cr, 'website_application', 'badge_quantity') \
                and get_field_exists(cr, 'website_application', 'foyer_members_count') \
                and get_field_exists(cr, 'website_application', 'home_type') \
                and get_field_exists(cr, 'website_application', 'residence_type') \
                and get_field_exists(cr, 'website_application', 'owner_type') \
                and get_field_exists(cr, 'website_application', 'lost_type'):

            cr.execute(
                "SELECT id, badge_quantity, foyer_members_count, home_type, residence_type, owner_type, lost_type"
                " FROM website_application WHERE type IN ("
                "'environment_support_request', 'environment_support_lost') ORDER BY id;")
        else:
            raise ProgrammingError
    except ProgrammingError:
        logger.info('Migration of informations ended: no applications to migrate.')
        return

    applications_before = cr.fetchall()

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Migration des anciennes applications vers les nouveaux templates
        for dict_application in applications_before:

            application = env['website.application'].browse(dict_application[0])

            if application.type == 'environment_support_request':
                if application.applicant_id.partner_id.is_company:
                    application.write({
                        'other_informations':
                            env.ref('environment_applications.application_information_number_of_badges').name +
                            ': ' + unicode(dict_application[1])
                    })

                else:
                    application.write({
                        'other_informations':
                            env.ref('environment_applications.application_information_foyer_members_count').name +
                            ': ' + unicode(dict_application[2]) + '<br />' +
                            env.ref('environment_applications.application_information_home_type').name +
                            ': ' + unicode(dict_application[3]) + '<br />' +
                            env.ref('environment_applications.application_information_residence_type').name +
                            ': ' + unicode(dict_application[4]) + '<br />' +
                            env.ref('environment_applications.application_information_owner_type').name +
                            ': ' + unicode(dict_application[5]) + '<br />'
                    })

            if application.type == 'environment_support_lost':
                application.write({
                    'other_informations':
                        env.ref('environment_applications.application_information_lost_type').name +
                        ': ' + unicode(dict_application[6])
                })

    logger.info('Migration of informations ended: %s application(s) migrated.' % len(applications_before))


def update_applications_documents(cr):
    logger.info('Migration of applications documents started.')

    try:
        if get_field_exists(cr, 'website_application', 'address_proof_id'):
            cr.execute("SELECT id, address_proof_id "
                       "FROM website_application "
                       "WHERE type IN ("
                       "'environment_support_request', 'environment_support_lost') "
                       "ORDER BY id;")
        else:
            raise ProgrammingError
    except ProgrammingError:
        logger.info('Migration of documents ended: no applications to migrate.')
        return

    applications_before = cr.fetchall()

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Migration des anciennes applications vers les nouveaux templates
        for dict_application in applications_before:
            if dict_application[1]:
                env['website.application'].browse(dict_application[0]).write({
                    'attachment_ids': [(6, 0, [dict_application[1]])],
                })

    logger.info('Migration of documents ended: %s application(s) migrated.' % len(applications_before))


def update_applications_type(cr):
    logger.info('Migration of applications informations started.')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        applications_before = env['website.application'].search([
            ('type', 'in', ['environment_support_request', 'environment_support_lost'])
        ])
        # Migration des anciennes applications vers les nouveaux templates
        for application in applications_before:

            if application.type == 'environment_support_request':
                if application.applicant_id.partner_id.is_company:
                    application.write({
                        'type': 'website_application_template',
                        'website_application_template_id':
                            env.ref('environment_applications.application_template_support_request_pro').id,
                    })

                else:
                    application.write({
                        'type': 'website_application_template',
                        'website_application_template_id':
                            env.ref('environment_applications.application_template_support_request_part').id,
                    })

            if application.type == 'environment_support_lost':
                application.write({
                    'type': 'website_application_template',
                    'website_application_template_id':
                        env.ref('environment_applications.application_template_support_loss').id,
                })

    logger.info('Migration of informations ended: %s application(s) migrated.' % len(applications_before))


def migrate(cr, version):
    """Migrate applications to application templates.

    As we created application templates which can contain all required data for applications of type
    environment_support_request and environment_support_lost, we need to migrate old created applications of that types.
    """
    logger.info('Migration started: migrating environment applications.')
    if not version:
        return

    update_templates_document_settings(cr)
    update_applications_informations(cr)
    update_applications_documents(cr)
    update_applications_type(cr)
    logger.info('Migration of environment applications ended.')


def get_field_exists(cr, table_name, field_name):
    result = False
    # check field existence

    try:
        sql = """SELECT count(*)
                 FROM pg_class c, pg_attribute a
                 WHERE c.relname = '{table}'
                 AND a.attname like '{field}'
                 AND c.oid=a.attrelid"""
        sql = sql.format(table=table_name, field=field_name)
        cr.execute(sql)

        if cr.fetchone()[0]:
            result = True
    except Exception as e:
        logger.error(e)

    return result
