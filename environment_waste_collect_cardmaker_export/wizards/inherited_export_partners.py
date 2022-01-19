# coding: utf-8

from odoo import models, fields


class PartnerExportWizard(models.TransientModel):
    _inherit = 'partner.contact.identification.cardmaker.export.wizard'

    use_license_plates = fields.Boolean(
        string="Use licence plates",
        help=("Does the cardmaker export wizard should add multiple lines for the same partner "
              "if it has multiple license plates?"),
    )

    def generate_partners_list(self):
        self.ensure_one()
        partners = super(PartnerExportWizard, self).generate_partners_list()

        use_license_plates = self.use_license_plates

        if not use_license_plates:
            return partners

        license_plate_identification_category = self.env.ref(
            'environment_waste_collect.horanet_license_plate_identification_category')

        updated_partners = []
        for partner in partners:
            license_plates = partner.mapped('id_numbers') \
                .filtered(lambda n: n.category_id == license_plate_identification_category)

            if not license_plates:
                updated_partners.append(partner)

            for j in range(len(license_plates)):
                updated_partners.append(partner)

        return updated_partners

    def action_export(self):
        model = super(PartnerExportWizard, self).action_export()

        mode = self.env['partner.contact.identification.cardmaker.export'].browse(model['res_id'])
        if self.use_license_plates:
            mode.write({
                'use_license_plates': True,
            })

        return model
