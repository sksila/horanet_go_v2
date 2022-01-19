# coding: utf-8

import logging

from psycopg2 import ProgrammingError

from odoo import api, SUPERUSER_ID

import unicodedata

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate applications to application templates.

    As we created application templates which can contain all required data for applications of type
    environment_support_request and environment_support_lost, we need to migrate old created applications of that types.
    """
    logger.info('Migration started: migrating environment applications.')
    if not version:
        return

    update_query_informations(cr)
    update_applications_informations(cr)
    logger.info('Migration of environment applications ended.')


def update_query_informations(cr):
    logger.info('Migration of query informations started.')

    if not get_field_exists(cr, 'application_information', 'name'):
        logger.info('Migration of query informations ended: no information to migrate.')
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        informations_before = env['application.information'].search([])

        # Migration des informations des anciennes applications vers le nouveau modèle
        for information in informations_before:
            technical_name = \
                unicodedata.normalize('NFD', information.name).encode('ascii', 'ignore').lower().replace(" ", "_")
            "".join([c for c in technical_name if c.isalnum() or c == '_'])

            information.write({
                'technical_name': technical_name
            })

    logger.info('Migration of query informations ended: %s information(s) migrated.' % len(informations_before))


def update_applications_informations(cr):
    logger.info('Migration of applications informations started.')

    try:
        if get_field_exists(cr, 'website_application', 'other_informations'):
            cr.execute(
                "SELECT id, other_informations "
                "FROM website_application WHERE type = 'website_application_template' ORDER BY id;")
        else:
            raise ProgrammingError
    except ProgrammingError:
        logger.info('Migration of informations ended: no applications to migrate.')
        return

    applications_before = cr.fetchall()

    if not applications_before:
        logger.info('Migration of informations ended: no applications to migrate.')
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        translated_names = {}
        # Migration des informations des anciennes applications vers le nouveau modèle
        for dict_application in applications_before:

            application = env['website.application'].browse(dict_application[0])
            old_informations = {}
            new_informations = []

            old_information = dict_application[1]
            if old_information:
                old_information = old_information.replace("<p>", "").replace("</p>", "")
                if len(old_information.split("<br />")) > 1:
                    infos = old_information.split("<br />")
                else:
                    infos = old_information.split("<br>")
                for info in infos:
                    if info:
                        info_values = info.split(":")
                        if len(info_values) == 2:
                            old_informations[info_values[0].strip()] = info_values[1].strip()

            query_informations = application.website_application_template_id.application_informations
            for query_information in query_informations:
                if not translated_names.get(query_information.name, False):
                    translated_name = env['ir.translation'].search([
                        ('src', '=', query_information.name),
                        ('name', '=', 'application.information,name'),
                    ], limit=1).value
                    translated_names[query_information.name] = translated_name

                new_information = query_information.copy({
                    'mode': 'result',
                })
                new_information.write({
                    'value': old_informations.get(query_information.name, False)
                    or old_informations.get(translated_names.get(query_information.name, ''), False) or ""
                })
                new_informations.append(new_information.id)

            application.write({'application_information_ids': [(6, 0, new_informations)]})

    logger.info('Migration of informations ended: %s application(s) migrated.' % len(applications_before))


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
