# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID
try:
    from odoo.addons.horanet_go.tools import migrations
except ImportError:
    from horanet_go.tools import migrations


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """The field time is added to improve the field create_date which was used as time."""
    if not version:
        return

    _logger.info('Start migration:')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Ajout d'un champ time sur le modèle pour remplacer le champ create_date, récupération des anciennes valeurs
        horanet_query_model = env['device.query']
        migrations.copy_column_to_column(env.cr, horanet_query_model._table, 'create_date', 'time')

        _logger.info('End migration')
