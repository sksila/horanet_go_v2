# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Class to override form_feedback method to pay invoices."""

    _inherit = 'payment.transaction'

    invoice_id = fields.Many2one(comodel_name='account.invoice', string='Invoice')

    @api.model
    def form_feedback(self, data, acquirer_name):
        """
        Override to confirm the sale order, if defined, and if the transaction is done.

        Create the payment if the transaction is ok.
        """
        tx = None
        res = super(PaymentTransaction, self).form_feedback(data, acquirer_name)

        # fetch the tx
        tx_find_method_name = '_%s_form_get_tx_from_data' % acquirer_name
        if hasattr(self, tx_find_method_name):
            tx = getattr(self, tx_find_method_name)(data)
        _logger.info('<%s> transaction processed: tx ref:%s, tx amount: %s', acquirer_name,
                     tx.reference if tx else 'n/a', tx.amount if tx else 'n/a')

        if not tx:
            return res

        # Variable nécessaire pour un dépôt
        trans_name = tx.reference.split('/')
        # If we make a deposit
        if trans_name[0] == "DEPO":
            tx._make_payment()
        # Si il y a un sale order
        elif tx.sale_order_id:
            # Auto-confirm SO if necessary
            tx._confirm_so(acquirer_name=acquirer_name)

        # Si la transaction est validée, on créé le paiement
        if tx.invoice_id and tx.state == 'done':
            # If we pay an invoice
            tx._confirm_invoice()

        return res

    def _confirm_invoice(self):
        """Confirm and pay the invoice or the invoice lines."""
        for tx in self:
            invoice = self.env['account.invoice'].search([('id', '=', tx.invoice_id.id)])
            if invoice:
                status = invoice.state
                if status == 'open':
                    if tx.acquirer_id.auto_confirm == 'generate_and_pay_invoice':
                        # On vérifie qu'il n'y a pas déjà un paiement avec cette transaction
                        payment = self.env['account.payment'].search([('payment_transaction_id', '=', tx.id)])
                        if not payment:
                            tx.invoice_id.pay_and_reconcile(tx.acquirer_id.journal_id, pay_amount=tx.amount)
                            # On récupère le paiement que l'on vient de faire et on lui colle la transaction
                            payment_id = tx.invoice_id.payment_ids\
                                .filtered(lambda r: not r.payment_transaction_id).sorted('create_date', reverse=True)[0]
                            payment_id.payment_transaction_id = tx.id
                        else:
                            _logger.warning("Transaction already paid for invoice : %s", tx.invoice_id.number)
                    else:
                        tx._make_payment()
                else:
                    _logger.warning("Invoice not in open state : %s", tx.invoice_id.number)
            else:
                _logger.warning("Failed to find the invoice %s", tx.invoice_id.number)

    def _make_payment(self):
        """Create the payment."""
        payment = self.env['account.payment'].sudo().create(
            {'name': u'DEPO {}'.format(self.partner_id.name),
             'payment_type': 'inbound',
             'partner_type': 'customer',
             'partner_id': self.partner_id.id,
             'journal_id': self.acquirer_id.journal_id.id,
             'amount': self.amount,
             'payment_transaction_id': self.id,
             'payment_method_id': self.acquirer_id.journal_id.inbound_payment_method_ids[0].id
             })
        payment.sudo().post()
