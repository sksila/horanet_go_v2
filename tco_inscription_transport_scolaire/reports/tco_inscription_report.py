# coding: utf8

from odoo import api, models


class TCOInscriptionReport(models.AbstractModel):
    _name = 'report.tco_inscription_transport_scolaire.global_report_view'

    @api.model
    def render_html(self, docids, data=None):
        u"""On surcharge la fonction pour ajouter l'image de fond du chèque transport."""
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(
            'tco_inscription_transport_scolaire.global_report_view'
        )

        ir_property_obj = self.env['ir.property']
        cheque_background_image = ir_property_obj.get(
            'cheque_background_image', 'horanet.transport.config')

        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(docids),
            'cheque_background_image': cheque_background_image,
        }

        return report_obj.render('tco_inscription_transport_scolaire.global_report_view', docargs)
