import logging

_logger = logging.getLogger(__name__)


def get_latest_moved_field(cr, table_name, field_name):
    """Permet de retrouver le champ (backup) d'Odoo lors d'un modification de nom de champ (attribute oldname).

    :param cr: database cursor (do not commit)
    :param table_name: le nom de la table du modèle (cf attribut _table_name)
    :param field_name: le nom du champ d'origine
    :return: None ou le nom de la colonne contenant le dernier backup
    """
    result = None
    # check field moved
    cr.execute("""SELECT count(*) FROM pg_class c,pg_attribute a
                  WHERE c.relname=%s
                    AND a.attname like %s
                    AND c.oid=a.attrelid """, (table_name, field_name + str('_moved%')))
    if cr.fetchone()[0]:
        i = 10
        while True:
            newname = field_name + '_moved' + str(i)
            cr.execute("""SELECT count(1)
                          FROM pg_class c,pg_attribute a
                          WHERE c.relname=%s
                            AND a.attname=%s
                            AND c.oid=a.attrelid """, (table_name, newname))
            if cr.fetchone()[0]:
                result = newname
                break
            i -= 1
            if i < 0:
                result = None
                break
    return result


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
        _logger.error(e)

    return result


def copy_column_to_column(cr, table_name, field_origin, field_destination):
    """Utility method used to copy field value in another field."""
    result = False
    try:
        sql = 'UPDATE {table_name} set {field_destination} = {field_origin}'.format(
            table_name=str(table_name),
            field_origin=str(field_origin),
            field_destination=str(field_destination)
        )
        cr.execute(sql)
    except Exception as e:
        _logger.error(e)
    return result
