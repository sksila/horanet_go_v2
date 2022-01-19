# coding: utf-8

import logging

from odoo import api, fields, models, exceptions

_logger = logging.getLogger(__name__)


class InscriptionCreateSOInvoice(models.TransientModel):
    """The wizard to create so and/or invoice for selected inscriptions."""

    _name = 'invoicing.wizard'

    @api.model
    def _get_default_inscriptions(self):
        active_ids = self.env.context.get('active_ids')
        if self.env.context.get('active_model') == 'tco.inscription.transport.scolaire' and active_ids:
            return self.env['tco.inscription.transport.scolaire'].browse(active_ids)

    inscription_ids = fields.Many2many(string='Inscriptions', comodel_name='tco.inscription.transport.scolaire',
                                       default=_get_default_inscriptions)
    action_type = fields.Selection(string="Type", selection=[('so', 'Sale order'),
                                                             ('so_invoice', 'Sale order and invoice')], default='so')
    validate_invoice = fields.Boolean(string="Validate invoice")
    ignore_documents = fields.Boolean(help="If activated, do not raise an error for missing documents")
    ignore_emails = fields.Boolean(help="Emails won't be sent at the validation of inscriptions")

    @api.multi
    def action_inscription_create_so_invoice(self):
        """Create so and/or invoice for inscriptions."""
        errors = []
        # Si aucune action n'est sélectionnée on ne fait rien
        if not self.action_type:
            return

        _logger.info("Starting computing inscriptions")

        # Dans tous les cas on créer le SO, mais seulement pour les bonnes inscriptions
        for inscription in self.inscription_ids.filtered(lambda r: r.status in ['draft', 'to_validate']):
            try:
                if not inscription.sale_order_ref:
                    if self.ignore_documents:
                        inscription.with_context({'force_creation': True}).action_create_saleorder()
                    else:
                        inscription.action_create_saleorder()

            except (exceptions.ValidationError, exceptions.MissingError) as e:
                print(e)
                errors.append(inscription.name)

        # Ensuite si demandé on crée les factures
        if self.action_type == 'so_invoice':
            so = self.inscription_ids.mapped('sale_order_ref')
            invoices = so.mapped('invoice_ids')
            new_invoices = so.filtered(lambda r: r.invoice_status == 'to invoice').action_invoice_create()
            invoices += self.env['account.invoice'].browse(new_invoices)

            # Si on demande à les valider, on valide le ou les invoices
            if self.validate_invoice and invoices:
                for invoice in invoices:
                    # Apparemment il peut y avoir un KeyError si on lance le wizard sur un grand nombre de record.
                    # Donc un try pour ne pas avoir à tout recommencer,
                    try:
                        invoice.with_context({'ignore_emails': True}).action_invoice_open()
                    except KeyError:
                        continue

        _logger.info("End of computing inscriptions")
