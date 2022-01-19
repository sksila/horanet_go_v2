# -*- coding: utf-8 -*-

# 1 : imports of python lib
# 2 :  imports of openerp
from odoo import models, fields, api


class InvoiceReportSettings(models.TransientModel):
    # region Private attributes
    _inherit = 'account.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    routeur_file_invoice_template = fields.Many2one(
        string="Invoice template for routeur file",
        comodel_name='ir.ui.view',
        help="Just the report with 'report_invoice', not 'document' in the name and mode is primary can be selected",
        domain="[('type', '=', 'qweb'),"
               " ('name', 'ilike', 'report_invoice'),"
               " ('name', 'not ilike', 'document'),"
               " ('mode', '=', 'primary'),"
               "]"
    )
    report_sepa_dynamic_elements = fields.Many2many(
        string="Dynamic elements",
        comodel_name='report.sepa.dynamic.element',
        help="Elements to add dynamically in invoice report SEPA",
    )
    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def get_default_routeur_file_invoice_template(self, _):
        """Return default values for routeur_file_invoice_template."""
        default = self.get_routeur_file_invoice_template_xml_id()
        return {
            'routeur_file_invoice_template': self.env.ref(default).id if default else False
        }

    @api.model
    def set_routeur_file_invoice_template(self):
        """Set the external ID of the report template."""
        icp = self.env['ir.config_parameter']
        icp.set_param(
            'account_invoice_report_sepa.default_routeur_file_invoice_template',
            self.routeur_file_invoice_template.xml_id
        )

    @api.model
    def get_routeur_file_invoice_template_xml_id(self):
        return self.env['ir.config_parameter'].get_param(
            'account_invoice_report_sepa.default_routeur_file_invoice_template', False
        )

    # endregion
