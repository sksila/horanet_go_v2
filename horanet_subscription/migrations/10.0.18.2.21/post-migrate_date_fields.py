# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Re-confirm subscriptions.

    As we transformed the state field into a computed field, and because for
    some reason, subscriptions don't have starting_date, let's re-confirm them.
    """
    if not version:
        return

    _logger.info('Start migration:')

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        models_name_to_migrate = ['horanet.subscription',
                                  'horanet.subscription.line',
                                  'horanet.package',
                                  'horanet.package.line']

        for model_name_to_migrate in models_name_to_migrate:
            model_obj = env[model_name_to_migrate]
            copy_column_to_column(env.cr, model_obj._table, 'start_date', 'opening_date')
            copy_column_to_column(env.cr, model_obj._table, 'end_date', 'closing_date')
            _logger.info('migration of {model_name}: {migrate_number}'.format(
                model_name=model_obj._name,
                migrate_number=str(model_obj.search_count([])))
            )

        _logger.info('End migration')


def copy_column_to_column(cr, table_name, field_origin, field_destination):
    try:
        sql = u'UPDATE {table_name} set {field_destination} = {field_origin}'.format(
            table_name=unicode(table_name),
            field_origin=unicode(field_origin),
            field_destination=unicode(field_destination)
        )
        cr.execute(sql)
    except Exception as e:
        _logger.error(e)
    return
