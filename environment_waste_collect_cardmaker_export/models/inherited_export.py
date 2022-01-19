# coding: utf-8

from odoo import models, api, fields


class CardMakerExport(models.Model):
    _inherit = 'partner.contact.identification.cardmaker.export'

    use_license_plates = fields.Boolean(string="Use license plates", default=False, readonly=True)

    @api.multi
    def create_assignations(self, partner_id, values):
        self.ensure_one()
        use_license_plates = self.use_license_plates

        if not use_license_plates:
            return super(CardMakerExport, self).create_assignations(partner_id, values)

        partner = self.env['res.partner'].browse(partner_id)

        license_plate_identification_category = self.env.ref(
            'environment_waste_collect.horanet_license_plate_identification_category')

        license_plates = partner.mapped('id_numbers') \
            .filtered(lambda n: n.category_id == license_plate_identification_category)

        tags = partner.mapped('tag_ids')

        for license_plate in license_plates:
            if license_plate.name in tags.mapped('external_reference'):
                continue

            values['external_reference'] = license_plate.name
            break

        super(CardMakerExport, self).create_assignations(partner_id, values)
