# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """The field time is added to improve the field create_date which was used as time."""
    if not version:
        return

    _logger.info('Start package migration:')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        package_model = env['horanet.package']
        packages_to_update = package_model.search([('prestation_id', '!=', False)])

        nb_packages = len(packages_to_update)
        _logger.info("{nb_packages} Package to migrate".format(nb_packages=str(nb_packages)))

        current = 0
        for package in packages_to_update:
            current += 1
            if not current % 1000:
                _logger.info("{current} Package migrated".format(current=str(current)))
            package.service_id = package.prestation_id.service_id

    _logger.info('End package migration')
