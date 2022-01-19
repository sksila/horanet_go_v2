# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging
import base64
# 2 :  imports of openerp
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class InvoiceReportHoranetRole(models.Model):
    """Surcharge du model horanet.role pour y ajouter le fichier routeur."""

    # region Private attributes
    _inherit = 'horanet.role'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    routeur_file_ids = fields.Many2many(string="Routeur files", comodel_name='ir.attachment', order='name')
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_create_routeur_file(self):
        """Create the routeur file."""
        invoices = self.env['account.move.line'].search([
            ('invoice_id.batch_id', '=', self.batch_id.id),
            ('date_maturity', '>=', self.date_declaration),
            ('debit', '>', 0.0),
            ('invoice_id', 'in', self.batch_id.invoice_ids.ids),
            ('invoice_id.state', '=', 'open'),
        ]).filtered(lambda aml: aml.get_ormc_debit() > 0.0).mapped('invoice_id')

        attachment_model = self.env['ir.attachment']
        routeur_file_ids = []

        template_xml_id = self.env['account.config.settings'].get_routeur_file_invoice_template_xml_id()

        if not template_xml_id:
            raise exceptions.UserError(_("Please Select a invoice template in the account settings"))

        offset = 0
        limit = 1000
        i = 0
        _logger.info("Starting creation of routeur file ({nb_total} invoices)".format(nb_total=str(len(invoices))))
        while offset < len(invoices):
            invoices_block = invoices[offset:min(offset + limit, len(invoices))]
            offset += limit
            i += 1
            _logger.info("Starting block {current_nb} of {nb_total}".format(
                current_nb=str(offset - limit) + '-' + str(offset),
                nb_total=str(len(invoices))
            ))

            pdf = self.env['report'].sudo().get_pdf(invoices_block.ids, template_xml_id)
            name = 'R' + str(self.id) + '-routeur-file-' + str(i)
            values = {
                'name': name,
                'document_type_id': self.env.ref('account_invoice_report_sepa.attachment_type_routeur_file').id,
                'datas': base64.b64encode(pdf),
                'datas_fname': name,
                'status': 'valid',
            }
            attachment = attachment_model.create(values)
            routeur_file_ids.append(attachment.id)

            # self.routeur_file = base64.b64encode(pdf)

        self.write({
            'routeur_file_ids': [(6, 0, routeur_file_ids)],
        })

        _logger.info("Ending creation of routeur file")

    # endregion

    # region Model methods
    # endregion

    pass
