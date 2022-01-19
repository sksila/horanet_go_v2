# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
import logging

__name__ = 'Change assignation partner_id to reference_id'
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # The new field reference_id cannot be converted (Many2one to Reference)
    # In this case, the system keep the old field and rename it to field_movedX
    # with X an increment
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        assignation_model = env['partner.contact.identification.assignation']
        reference_id_old = get_latest_moved_field(env.cr, assignation_model._table, 'reference_id')
        if reference_id_old:
            _logger.info("Convert value, from M2O res.partner to Reference. START")
            # update value from M2O to reference
            sql = "UPDATE {table} SET reference_id = CONCAT('res.partner,', {moved}) WHERE {moved} is not NULL"
            sql = sql.format(table=assignation_model._table, moved=reference_id_old)
            cr.execute(sql)
            # clean old value to save space (keep the column) and assure correct cascading migration
            sql = "UPDATE {table} SET {moved} = NULL"
            sql = sql.format(table=assignation_model._table, moved=reference_id_old)
            cr.execute(sql)
            _logger.info("Convert value, from M2O res.partner to Reference. DONE")


def get_latest_moved_field(cr, table_name, field_name):
    result = None
    # check field moved
    cr.execute("SELECT count(*) FROM pg_class c,pg_attribute a "
               "WHERE c.relname=%s "
               "AND a.attname like %s "
               "AND c.oid=a.attrelid ", (table_name, field_name + str('_moved%')))
    if cr.fetchone()[0]:
        i = 10
        while True:
            newname = field_name + '_moved' + str(i)
            cr.execute("SELECT count(1) FROM pg_class c,pg_attribute a "
                       "WHERE c.relname=%s "
                       "AND a.attname=%s "
                       "AND c.oid=a.attrelid ", (table_name, newname))
            if cr.fetchone()[0]:
                result = newname
                break
            i -= 1
            if i < 0:
                result = None
                break
    return result
