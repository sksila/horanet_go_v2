# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Relink tags to fresh created mappings.

    Load generated data file to link all tags to new mappings
    """
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Passage du field type char en selection
        mapping_model = env['partner.contact.identification.mapping']
        to_rename_red = mapping_model.search([('mapping', '=ilike', 'h3')])
        if to_rename_red:
            _logger.info("Rename field mapping on mapping records (" +
                         ','.join([str(id) for id in to_rename_red.ids]) + ") to h3")
            to_rename_red.write({'mapping': 'h3'})
        to_rename_red = mapping_model.search([('mapping', '!=', 'h3')])
        if to_rename_red:
            _logger.info("Rename field mapping on mapping records (" +
                         ','.join([str(id) for id in to_rename_red.ids]) + ") to csn")
            to_rename_red.write({'mapping': 'csn'})

        # Transformation des éventuelles area 'transport' en horanet (data)
        area_transport = env['partner.contact.identification.area'].search([('name', 'ilike', 'transport')])
        if area_transport:
            to_alter_rec = mapping_model.search([('area_id', '=', area_transport.id)])
            if to_alter_rec:
                _logger.info(
                    "Rename old area transport to horanet on mapping recs (" +
                    ','.join([str(id) for id in to_alter_rec.ids]) + ")")
                to_alter_rec.write({'area_id': env.ref('partner_contact_identification.area_horanet').id})
            area_transport.unlink()
