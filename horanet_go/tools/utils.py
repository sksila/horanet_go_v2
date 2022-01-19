from contextlib import contextmanager
from odoo import api, models


@contextmanager
def safe_environment(environment, uid=None):
    """Return an environment with a new test cursor for the current environment database.

    the cursor will never be committed (thus preventing any alteration on the DB)
    but will be closed after the context block.
    """
    if not hasattr(environment, 'registry'):
        raise AttributeError('This method is meant to be called with an Odoo environment')

    try:
        environment.registry.enter_test_mode()
        yield api.Environment(environment.registry.test_cr, uid or environment.uid, environment.context)
    finally:
        environment.registry.leave_test_mode()

    pass


def format_log(log):
    """Utility method to easily inject some formatting in an HTML displayed field."""
    log = log.replace('\n', '<br>').replace('\t', '&emsp;')
    log = log.replace('<error>', '<span class=\"bg-danger\">').replace('</error>', '</span>')
    log = log.replace('<warning>', '<span class=\"bg-warning\">').replace('</warning>', '</span>')
    log = log.replace('<info>', '<span class=\"bg-info\">').replace('</info>', '</span>')
    return log


def get_record_values(record, related=False):
    """Get from a record the values dictionary needed to create a copy of the record.

    This method is used to create a record from an 'new' record (a record in cache without ID)

    :param record: An ORM object (record)
    :param related: If True, get the related fields of the object
    :return: A dictionary of <field_name : value>
    """
    if not isinstance(record, models.Model):
        raise AttributeError('The parameter record must be a model')
    record.ensure_one()
    return dict({(key, isinstance(record[key], models.Model) and (record[key].id or record[key].ids) or record[key])
                 for key, value in list(record._fields.items())
                 if not (key.startswith('_')
                         or key in models.MAGIC_COLUMNS
                         or (not related and value.related)
                         or isinstance(record[key], models.Model) and not record[key].ids)})


def clear_context_default_value(context):
    """Return a new context without the default keys."""
    return {
        key: val
        for key, val in list(context.items())
        if not (isinstance(key, str) and key.startswith('default_'))
        }
