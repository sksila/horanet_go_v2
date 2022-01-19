# coding: utf-8

import logging

from psycopg2 import ProgrammingError

from odoo import api, SUPERUSER_ID

logger = logging.getLogger(__name__)

REMOVAL_REASONS = dict([
    ('move', 'Déménagement '),
    ('sw_school', 'Changement d\'établissement scolaire'),
    ('stage', 'Absence prolongée pour stage'),
    ('sickness', 'Absence prolongée pour maladie'),
    ('other', 'Autres')])

REFUND_TYPES = dict([('refund', 'Avoir'), ('exoneration', 'Exonération')])


def migrate(cr, version):
    """Migrate TCO applications to application templates.

    As we created application templates which can contain all required data for applications of type
    tco_removal, tco_refund and tco_path_modification, we need to migrate old created applications of that types.
    """
    logger.info('Migration started: migrating TCO applications.')
    if not version:
        return

    update_tco_applications_informations(cr)
    update_applications_documents(cr)
    update_applications_type(cr)
    logger.info('Migration of TCO applications ended.')


def update_tco_applications_informations(cr):
    logger.info('Migration of TCO applications informations started.')

    try:

        if get_field_exists(cr, 'website_application', 'inscription_id') \
                and get_field_exists(cr, 'website_application', 'removal_reason') \
                and get_field_exists(cr, 'website_application', 'on_date') \
                and get_field_exists(cr, 'website_application', 'refund_type') \
                and get_field_exists(cr, 'website_application', 'date_changing_residence') \
                and get_field_exists(cr, 'website_application', 'date_changing_establishment') \
                and get_field_exists(cr, 'website_application', 'type'):

            cr.execute(
                "SELECT id, inscription_id, removal_reason, on_date, refund_type, "
                "date_changing_residence, date_changing_establishment, type "
                "FROM website_application "
                "WHERE type IN ('tco_removal','tco_refund','tco_path_modification') ORDER BY id;")
        else:
            raise ProgrammingError
    except ProgrammingError:
        logger.info('Migration of tTCO applications informations ended: no applications to migrate.')
        return

    applications_before = cr.fetchall()

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Migration des anciennes applications vers les nouveaux templates
        for dict_application in applications_before:

            application = env['website.application'].browse(dict_application[0])
            type = dict_application[7]

            new_informations = []

            new_information = env.ref('tco_inscription_transport_scolaire.application_information_inscription_id') \
                .copy({'mode': 'result'})
            new_information.write({'value': str(dict_application[1])})
            new_informations.append(new_information.id)

            if type == 'tco_removal':
                new_information = env.ref('tco_inscription_transport_scolaire.application_information_removal_reason')\
                    .copy({'mode': 'result'})
                new_information.write({'value': REMOVAL_REASONS[dict_application[2]]})
                new_informations.append(new_information.id)

                new_information = env.ref('tco_inscription_transport_scolaire.application_information_on_date')\
                    .copy({'mode': 'result'})
                new_information.write({'value': str(dict_application[3])})
                new_informations.append(new_information.id)

            if type == 'tco_refund':
                new_information = env.ref('tco_inscription_transport_scolaire.application_information_removal_reason')\
                    .copy({'mode': 'result'})
                new_information.write({'value': REMOVAL_REASONS[dict_application[2]]})
                new_informations.append(new_information.id)

                new_information = env.ref('tco_inscription_transport_scolaire.application_information_on_date')\
                    .copy({'mode': 'result'})
                new_information.write({'value': str(dict_application[3])})
                new_informations.append(new_information.id)

                new_information = env.ref('tco_inscription_transport_scolaire.application_information_refund_type')\
                    .copy({'mode': 'result'})
                new_information.write({'value': REFUND_TYPES[dict_application[4]]})
                new_informations.append(new_information.id)

            if type == 'tco_path_modification':
                if dict_application[5]:
                    new_information = \
                      env.ref('tco_inscription_transport_scolaire.application_information_date_changing_residence')\
                      .copy({'mode': 'result'})
                    new_information.write({'value': str(dict_application[5])})
                    new_informations.append(new_information.id)

                if dict_application[6]:
                    new_information = \
                      env.ref('tco_inscription_transport_scolaire.application_information_date_changing_establishment')\
                      .copy({'mode': 'result'})
                    new_information.write({'value': str(dict_application[6])})
                    new_informations.append(new_information.id)

            application.write({'application_information_ids': [(6, 0, new_informations)]})

    logger.info('Migration of TCO applications infos ended: %s application(s) migrated.' % len(applications_before))


def update_applications_documents(cr):
    logger.info('Migration of applications documents started.')

    try:
        if get_field_exists(cr, 'website_application', 'proof_document') and \
           get_field_exists(cr, 'website_application', 'proof_document_name') and \
           get_field_exists(cr, 'website_application', 'proof_document2') and \
           get_field_exists(cr, 'website_application', 'proof_document_name2'):
            cr.execute("SELECT id, proof_document, proof_document_name, proof_document2, proof_document_name2 "
                       "FROM website_application "
                       "WHERE type IN ('tco_removal','tco_refund','tco_path_modification') "
                       "ORDER BY id;")
        else:
            raise ProgrammingError
    except ProgrammingError:
        logger.info('Migration of documents ended: no applications to migrate.')
        return

    applications_before = cr.fetchall()

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        attachment_model = env['ir.attachment'].sudo()

        # Migration des anciennes applications vers les nouveaux templates
        for dict_application in applications_before:

            application = env['website.application'].browse(dict_application[0])

            attachment_ids = []
            if dict_application[1]:
                values = {
                    'document_type_id': env.ref('tco_inscription_transport_scolaire.attachment_type_proof').id,
                    'datas': dict_application[1],
                    'datas_fname': dict_application[2],
                    'user_id': application.applicant_id.id,
                    'partner_id': application.applicant_id.partner_id.id
                }
                if application.state == 'accepted':
                    values['status'] = 'valid'
                if application.state == 'rejected':
                    values['status'] = 'rejected'
                attachment = attachment_model.create(values)
                attachment_ids.append(attachment.id)

            if dict_application[3]:
                values = {
                    'document_type_id': env.ref('tco_inscription_transport_scolaire.attachment_type_proof').id,
                    'datas': dict_application[3],
                    'datas_fname': dict_application[4],
                    'user_id': application.applicant_id.id,
                    'partner_id': application.applicant_id.partner_id.id
                }
                if application.state == 'accepted':
                    values['status'] = 'valid'
                if application.state == 'rejected':
                    values['status'] = 'rejected'
                attachment = attachment_model.create(values)
                attachment_ids.append(attachment.id)

            application.write({
                'attachment_ids': [(6, 0, attachment_ids)],
            })

    logger.info('Migration of documents ended: %s application(s) migrated.' % len(applications_before))


def update_applications_type(cr):
    logger.info('Migration of applications types started.')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        try:
            if get_field_exists(cr, 'website_application', 'type'):
                cr.execute("SELECT id, type "
                           "FROM website_application "
                           "WHERE type IN ('tco_removal','tco_refund','tco_path_modification') "
                           "ORDER BY id;")
            else:
                raise ProgrammingError
        except ProgrammingError:
            logger.info('Migration of applications types ended: no applications to migrate.')
            return

        applications_before = cr.fetchall()

        with api.Environment.manage():
            env = api.Environment(cr, SUPERUSER_ID, {})

            # Migration des anciennes applications vers les nouveaux templates
            for dict_application in applications_before:
                application = env['website.application'].browse(dict_application[0])
                type = dict_application[1]

                if type == 'tco_removal':
                    application.write({
                        'website_application_template_id':
                            env.ref('tco_inscription_transport_scolaire.application_template_tco_removal').id,
                    })

                if type == 'tco_refund':
                    application.write({
                        'website_application_template_id':
                            env.ref('tco_inscription_transport_scolaire.application_template_tco_refund').id,
                    })

                if type == 'tco_path_modification':
                    application.write({
                        'website_application_template_id':
                            env.ref('tco_inscription_transport_scolaire.application_template_tco_path_modification').id,
                    })

    logger.info('Migration of applications types ended: %s application(s) migrated.' % len(applications_before))


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
