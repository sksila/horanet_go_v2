# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate field 'code' of technology."""
    if not version:
        return

    _logger.info('Start technology migration:')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        technology_model = env['partner.contact.identification.technology']
        technologies = technology_model.search([('code', '=', False)])

        # Par défaut, on met le code le même que le nom en minuscule
        for technology in technologies:
            technology.code = technology.name.strip(' ').upper()

    _logger.info('End technology migration')
