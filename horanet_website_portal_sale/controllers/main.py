# -*- coding: utf-8 -*-

import json

from odoo.addons.website_payment.controllers.main import WebsitePayment
from odoo.addons.website_portal.controllers.main import website_account

from odoo import fields
from odoo import http
from odoo.http import request, route
from odoo.tools.translate import _


class CustomWebsitePayment(WebsitePayment):
    """Override 2 functions to add the invoice in the data."""

    @http.route(['/website_payment/pay'], type='http', auth='public', website=True)
    def pay(self, reference='', amount=False, currency_id=None, acquirer_id=None, **kw):
        """
        Generate the all datas to create the transaction and add the invoice number in the values.

        :param reference: reference of the invoice
        :param amount: amount paid
        :param currency_id: the currency
        :param acquirer_id: the acquirer
        :param kw: kw
        """
        response = super(CustomWebsitePayment, self).pay(reference, amount, currency_id, acquirer_id, **kw)

        response.qcontext.update({'invoice_ref': reference})

        return response

    @http.route(['/website_payment/transaction'], type='json', auth="public", website=True)
    def transaction(self, reference, amount, currency_id, acquirer_id, invoice_ref):
        """
        Create the transaction with all the data and add the invoice number in the transaction.

        :param reference: the reference of the transaction
        :param amount: amount paid
        :param currency_id: currency
        :param acquirer_id: the acquirer
        :param invoice: the number of the invoice
        :return: transaction id
        """
        tx_id = super(CustomWebsitePayment, self).transaction(reference, amount, currency_id, acquirer_id)

        transaction = request.env['payment.transaction'].sudo().browse(tx_id)
        invoice = request.env['account.invoice'].search([('number', '=', invoice_ref)]) or False

        transaction.write({'invoice_id': invoice.id})
        return transaction.id


class PortalSaleWebsiteAccount(website_account):
    def _get_payzen(self):
        """Return payment.acquirer corresponding to Payzen."""
        acquirer_obj = request.env['payment.acquirer']

        return acquirer_obj.search([('name', '=', 'Payzen')])

    def _compute_invoices_amount(self, invoices):
        """Compute the total amount of each invoices.

        :param account.invoice invoices: invoices to iterate on
        """
        amount = 0

        for invoice in invoices:
            amount += invoice.residual

        return amount

    def _compute_move_lines_amount(self, move_lines):
        """Compute the total amount of each move lines.

        :param account.move.line move_lines: move lines to iterate on
        """
        amount = 0

        for move_line in move_lines:
            amount += move_line.amount_residual

        return amount

    def _update_transaction_values(self, amount, reference, currency_id, partner_id, country_id, invoice_id):
        """Return a dictionnay with values used to create a payment.transaction.

        :param float amount: the amount of the transaction
        :param str reference: the reference of the voucher
        :param res.currency currency_id: currency used for the transaction
        :param res.partner partner_id: partner used for the transaction
        :param res.country country_id: country used for the transaction
        :param account.voucher voucher_ids: voucher(s) used for the transaction
        """
        return {
            'amount': amount,
            'reference': reference,
            'currency_id': currency_id,
            'partner_id': partner_id,
            'partner_country_id': country_id,
            'invoice_id': invoice_id.id,
        }

    @http.route()
    def account(self, **kw):
        """Add deposit amount on the main page."""
        response = super(PortalSaleWebsiteAccount, self).account(**kw)

        user_invoices = request.env['account.invoice'].search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', '=', 'open')
        ])

        advance_account_balance = request.env.user.credit
        for invoice in user_invoices:
            advance_account_balance -= invoice.residual

        response.qcontext.update({
            'advance_account_balance': advance_account_balance,
        })
        return response

    @route(['/my/deposit/add-credit'], type='http', auth='user', website=True)
    def add_credit(self):
        """Display a template to enter the amount to credit to the user's advance account."""
        template_name = 'horanet_website_portal_sale.add_credit'
        context = {
            'user': request.env.user
        }

        return request.render(template_name, context)

    @http.route(['/my/deposit'], type='http', auth="user", website=True)
    def my_deposit(self):
        """Render a template to show the deposit account of the user."""
        values = self._prepare_portal_layout_values()
        user_invoices = request.env['account.invoice'].search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', '=', 'open')
        ])

        advance_account_balance = request.env.user.credit
        for invoice in user_invoices:
            advance_account_balance -= invoice.residual

        values.update({
            'advance_account_balance': advance_account_balance,
        })
        return request.render('horanet_website_portal_sale.deposit_account', values)

    @route(['/my/payment'], type='http', auth='user', method=['POST'], website=True)
    def payment(self, **kw):
        """Display a page that contains necessary informations about the payment that will be processed.

        :param dict kw: arguments passed to the route via POST call
        """
        payzen = self._get_payzen()
        template_name = 'horanet_website_portal_sale.confirm_payment'
        context = {
            'acquirer_id': payzen.id,
            'payzen_url': payzen.payzen_get_form_action_url(),
        }

        # Deposit amount
        if 'deposit_amount' in kw.keys():
            user = request.env.user
            amount = kw.get('deposit_amount')
            if amount and amount != '0.0' and amount != '0':
                context.update({
                    'user': user,
                    'amount_total': float(kw.get('deposit_amount').replace(',', '.')),
                    'currency': user.partner_id.company_id.currency_id.name,
                    'action': 'deposit',
                })

                return request.render(template_name, context)
            else:
                context.update({
                    'user': user,
                    'alert_error': True
                })
                return request.render('horanet_website_portal_sale.add_credit', context)

        return request.render(template_name, context)

    @route(['/my/home/payment/transaction/'], type='json', auth='user', website=True)
    def payment_transaction(self, acquirer_id, **kw):
        """Json method that creates a payment.transaction.

            Used to create a transaction when the user clicks on 'pay now' button. After having
            created the transaction, the event continues and the user is redirected
            to the acquirer website.

        :param int acquirer_id: id of a payment.acquirer record. If not set the
                                user is redirected to the checkout page
        :param int acquirer_id: id of the acquirer used to render the form
        :param dict kw: arguments passed to the route via JSON-RPC call
        """
        if not acquirer_id:
            return request.redirect('/my/home')

        transaction_obj = request.env['payment.transaction']

        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        reference = kw.get('reference', False)

        # Will be passed to transaction_obj to create a record
        transaction_values = {
            'acquirer_id': acquirer.id,
            'type': 'form',
        }

        # If we make a deposit
        if 'deposit' in kw.get('action'):
            user = request.env.user
            amount = kw.get('amount')
            reference = transaction_obj.get_next_reference(u'DEPO/{}'.format(user.partner_id.name).replace(' ', ''))
            transaction_values.update(self._update_transaction_values(
                amount, reference, user.company_id.currency_id.id, user.partner_id.id,
                user.partner_id.country_id, request.env['account.invoice']))

        # If we pay invoice line
        elif kw.get('action') == 'pay_invoice_line':
            invoice = request.env['account.invoice'].sudo().browse(kw.get('invoice_id'))
            move_lines = request.env['account.move.line'].sudo().browse(
                json.loads(kw.get('move_line_ids'))
            )

            amount = kw.get('amount', False) or self._compute_move_lines_amount(move_lines)

            # Doing this ensure that the reference of the transaction will
            # always be unique
            if not reference:
                reference = transaction_obj.get_next_reference(invoice.number)

            transaction_values.update(self._update_transaction_values(
                amount, reference, invoice.currency_id.id, invoice.partner_id.id,
                invoice.partner_id.country_id, invoice))

        transaction = transaction_obj.sudo().create(transaction_values)
        request.session['website_payment_tx_id'] = transaction.id

        return transaction.id

    @route(['/my/home/payment/validate'], type='http', auth='user', method=['POST'], website=True)
    def payment_validate(self, **kw):
        """Display a summary page about the payment that have been processed.

        :param kw: arguments passed to the route via POST call
        """
        if 'vads_trans_status' not in kw:
            return request.redirect('/my/home')

        template_name = 'horanet_website_portal_sale.payment_validate'

        paid_amount = kw['vads_amount'].encode('utf-8')
        length_paid = len(paid_amount)

        context = {
            'transaction_status': kw['vads_trans_status'].encode('utf-8'),
            'paid_amount': float(paid_amount[:length_paid - 2] + '.' + paid_amount[length_paid - 2:]),
            'action': 'pay_invoice'
        }

        if 'invoice_ids' in request.session:
            invoices = request.env['account.invoice'].browse(request.session['invoice_ids'])
            context['invoices'] = invoices
            del request.session['invoice_ids']
        else:
            context.update({
                'user': request.env.user,
                'action': 'deposit'
            })
            context['user'] = request.env.user

        return request.render(template_name, context)

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, **kw):
        """Display a list of partner's invoices and payments.

        :param page: number of available pages
        :param date_begin: begin date to filter results
        :param date_end: end date to filter results
        :param kw: additional parameters
        """
        response = super(PortalSaleWebsiteAccount, self).portal_my_invoices(page, date_begin, date_end, **kw)

        partner_invoices = response.qcontext.get('invoices') \
            .filtered(lambda r: r.partner_id == request.env.user.partner_id)
        response.qcontext.update({'invoices': partner_invoices})

        domain = [
            ('website_published', '=', True),
            ('company_id', '=', request.env.user.company_id.id),
            ('journal_id', '!=', False)
        ]

        acquirer_ids = request.env['payment.acquirer'].sudo().search(domain)

        if acquirer_ids:
            response.qcontext.update({'available_acquirer': True})
        else:
            response.qcontext.update({'available_acquirer': False})

        return response

    @route(['/my/invoice/<int:invoice_id>'], type='http', auth='user', method=['GET', 'POST'], website=True)
    def get_invoice(self, invoice_id, **kw):
        """Display schedules of the invoice.

        :param int invoice_id: id of the invoice to display
        :param dict kw: arguments passed to the route via GET or POST call
        """
        user = request.env.user
        invoice = request.env['account.invoice'].sudo().browse(invoice_id)

        if not invoice.exists():
            return request.redirect('/my/home')

        template_name = 'horanet_website_portal_sale.invoice'
        context = {
            'invoice': invoice,
            'tools': request.env['res.lang'],
            'current_date': fields.Date.today(),
            'move_line_ids': None,
            'error': None,
            'payment_ready': False
        }

        if request.httprequest.method == 'POST':
            invoice_move_lines = invoice.mapped('move_id.line_ids') \
                .filtered(lambda r: not r.full_reconcile_id and r.date_maturity and not r.credit) \
                .sorted(key=lambda r: r.date_maturity).ids

            move_line_ids = [x.encode('utf-8') for x in kw.get('move_line_ids').split(',')]
            selected_move_lines = None
            try:
                selected_move_lines = map(int, move_line_ids)
                error = self._validate_form_pay_move_lines(selected_move_lines, invoice_move_lines)
            except ValueError:
                error = _('You did not select any schedule to pay.')

            if not error:
                # Try default one then fallback on first
                move_lines = request.env['account.move.line'].sudo().browse(selected_move_lines)
                acquirer_id = \
                    request.env['ir.values'].get_default('payment.transaction', 'acquirer_id',
                                                         company_id=user.company_id.id) \
                    or request.env['payment.acquirer'].search(
                        [('website_published', '=', True), ('company_id', '=', user.company_id.id)])[0].id

                acquirer = request.env['payment.acquirer'].with_context(submit_class='btn btn-primary pull-right',
                                                                        submit_txt=_('Pay Now')).browse(acquirer_id)
                reference = request.env['payment.transaction'].get_next_reference(invoice.number)
                amount_total = self._compute_move_lines_amount(move_lines)
                payment_form = acquirer.sudo().render(reference, float(amount_total), user.company_id.currency_id.id,
                                                      values={'return_url': '/website_payment/confirm',
                                                              'partner_id': user.partner_id.id})

                context = {
                    'acquirer_id': acquirer.id,
                    'payment_form': payment_form,
                    'reference': reference,
                    'invoice': invoice,
                    'move_line_ids': selected_move_lines,
                    'amount_total': amount_total,
                    'action': 'pay_invoice_line',
                    'payment_ready': True
                }

                # Useful when the user come back from payzen to display if the
                # transaction was successful or not
                request.session['invoice_ids'] = invoice.id

                return request.render(template_name, context)

            context.update({
                'move_line_ids': selected_move_lines,
                'error': error
            })

        return request.render(template_name, context)

    def _validate_form_pay_move_lines(self, selected_move_lines, invoice_move_lines):
        """Check if selected move lines are in the calendar order.

        :param list(int) selected_move_lines: ids of selected move lines
        :param list(int) invoice_move_lines: ids of invoice's move lines
        """
        error = None

        if selected_move_lines[0] != invoice_move_lines[0]:
            error = _('You cannot pay a schedule before its predecessors.')
        elif len(selected_move_lines) > 1:
            for i, move_line in enumerate(selected_move_lines):
                if move_line != invoice_move_lines[i]:
                    error = _('You cannot pay a schedule before its predecessors.')
                    break

        return error
