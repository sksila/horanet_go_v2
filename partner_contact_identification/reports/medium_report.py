
from odoo import api, fields, models


class MediumReport(models.AbstractModel):
    _name = 'report.partner_contact_identification.medium_report_template'

    @api.model
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name(
            'partner_contact_identification.medium_report_template'
        )

        ir_property_obj = self.env['ir.property']
        medium_recto_image = ir_property_obj.get(
            'medium_recto_image', 'res.config.settings')

        medium_verso_image = ir_property_obj.get(
            'medium_verso_image', 'res.config.settings')

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(docids),
            'medium_recto_image': medium_recto_image,
            'medium_verso_image': medium_verso_image,
        }
