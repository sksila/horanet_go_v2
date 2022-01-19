# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID
try:
    from odoo.addons.horanet_subscription.tools import date_utils
except ImportError:
    from horanet_subscription.tools import date_utils


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migrate assignation end date.

    At the beginning of the model assignation, its end_date field was a Date field and end_assignation function filled
    it with fields.Date.today().
    Then, end_date field changed to Datetime field but end_assignation function didn't change.
    So there are assignations
    - whose end_date are inferior to start_date.
    - whose end_date is at 1:00 or 2:00
    """
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        production_point_module = env['ir.module.module'].search([('name', '=', 'environment_production_point')])
        if production_point_module and production_point_module.state == 'to upgrade':
            _logger.info("Assignation end date migration will be made by environment_production_point module")
            return

    # 1 - Force end_date to start _date if end_date < start_date
    cr.execute("SELECT id FROM partner_contact_identification_assignation WHERE end_date < start_date ORDER BY id;")

    assignation_ids = [a[0] for a in cr.fetchall()]

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        assignation_model = env['partner.contact.identification.assignation']
        assignations = assignation_model.browse(assignation_ids)

        for assignation in assignations:
            try:
                assignation.write({
                    'end_date': assignation.start_date
                })
            except:
                assignation.unlink()

    # 2 - Force end_date to end of day if end_date and hour of end_date is 00:00:00
    cr.execute("""SELECT id FROM partner_contact_identification_assignation
                  WHERE end_date IS NOT NULL AND date_part('hour', end_date) = 0 ORDER BY id;""")

    assignation_ids = [a[0] for a in cr.fetchall()]

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        assignation_model = env['partner.contact.identification.assignation']
        assignations = assignation_model.browse(assignation_ids)

        for assignation in assignations:
            new_end_date = date_utils.convert_date_to_closing_datetime(assignation.end_date[0:10])
            same_day_assignation = assignation_model.search([
                ('id', '!=', assignation.id),
                ('is_active', '=', True),
                ('start_date', '>', assignation.end_date),
                ('start_date', '<', new_end_date.strftime('%Y-%m-%d %H:%M:%S')),
                '|',
                ('tag_id', '=', assignation.tag_id.id),
                ('reference_id', '=', assignation.reference_id and '%s,%d' % (
                    assignation.reference_id._name, assignation.reference_id.id) or False),
            ], order='start_date', limit=1)

            assignation.write({
                'end_date': same_day_assignation and same_day_assignation.start_date or new_end_date
            })

    _logger.info("End assignation end date migration")
