# coding: utf-8

import logging

from odoo.addons.horanet_go.tools import migrations

from odoo import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Delete old sequence partner.company_title.

    And update field partner.title with old value company_title
    """
    if not version:
        return
    with api.Environment.manage():

        env = api.Environment(cr, SUPERUSER_ID, {})

        if not migrations.get_field_exists(env.cr, 'res_partner', 'company_title'):
            return

        logger.info('******* Migration started: migrating partner company_title ******* ')

        # Create a mapping between old value and new title record
        mapping_dict = {
            'sarl': env.ref('horanet_go.company_title_SARL').id,
            'sas': env.ref('horanet_go.company_title_SAS').id,
            'sa': env.ref('horanet_go.company_title_SA').id,
            'ae': env.ref('horanet_go.company_title_AE').id,
            'ei': env.ref('horanet_go.company_title_EI').id,
            'eurl': env.ref('horanet_go.company_title_EURL').id,
            'gaec': env.ref('horanet_go.company_title_GAEC').id,
            'sci': env.ref('horanet_go.company_title_SCI').id,
            'cesu': env.ref('horanet_go.company_title_CESU').id,
            'trader': env.ref('horanet_go.company_title_commercant').id,
            'craftsman': env.ref('horanet_go.company_title_craftsman').id,
        }

        for key, value in mapping_dict.items():
            env.cr.execute("UPDATE res_partner set title={title_id} where company_title = '{company_title}'".format(
                title_id=value,
                company_title=key,
            ))

        logger.info('******* Migration ended ******* ')
