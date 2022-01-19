# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID

try:
    from odoo.addons.horanet_go.tools import migrations
except ImportError:
    from horanet_go.tools import migrations

__name__ = 'Set barcode technology record as data, not demo data.'


def migrate(cr, version):
    """Set barcode technology record as data, not demo data."""
    if not version:
        return

    if not migrations.get_field_exists(cr, 'partner_contact_identification_technology', 'code'):
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        ir_data_model = env['ir.model.data']
        demo_barcode_identifier = ir_data_model.search([
            ('module', '=', 'partner_contact_identification'),
            ('name', '=', 'demo_technology_barcode'),
        ])
        new_barcode_identifier = ir_data_model.search([
            ('module', '=', 'partner_contact_identification'),
            ('name', '=', 'technology_barcode'),
        ])

        sql = "SELECT id FROM {table} WHERE code='{code}'"
        sql = sql.format(table='partner_contact_identification_technology', code='Barcode')
        cr.execute(sql)

        barcode_id = False
        record = cr.fetchone()
        if record:
            barcode_id = record[0]

        if demo_barcode_identifier:
            demo_barcode_identifier.write({
                'name': 'technology_barcode',
            })
        elif not new_barcode_identifier and barcode_id:
            ir_data_model.create({
                'module': 'partner_contact_identification',
                'model': 'partner.contact.identification.technology',
                'res_id': barcode_id,
                'name': 'technology_barcode',
                'noupdate': True
            })
