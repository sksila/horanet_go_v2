# -*- coding: utf-8 -*-

import re

from odoo import models, api, fields


class InheritedAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_usages_from_invoice(self):
        """
        Get all usages from an invoice.

        :return: a list of usages
        """
        if self.subscription_id:
            ids_package_line = self.env['horanet.package.line'].search([
                ('subscription_id', '=', self.subscription_id.id),
                ('opening_date', '>=', str(self.get_accounting_year() - 1) + '-01-01'),
                '|',
                '&',
                ('package_id.invoice_type', '=', 'ending'),
                ('closing_date', '<=', str(self.date_due or fields.Date.today())),
                '&',
                ('package_id.invoice_type', 'not in', ['ending']),  # 'beginning' or None
                ('closing_date', '<=', str(self.get_accounting_year()) + '-12-31')
            ]).ids
            return self.env['horanet.usage'].search([
                ('package_line_id', 'in', ids_package_line),
            ], order='usage_date')
        else:
            return self.usage_ids

    def get_subscription_line(self, invoice_line):
        """
        Get the subscription line from an invoice line.

        :param invoice_line: the invoice line
        :return: the subscription line
        """
        if invoice_line:
            sol = self.env['sale.order.line'].search([('invoice_lines', 'in', invoice_line.id)])
            so = sol and sol[0].order_id

            if so:
                subscription_line = self.env['horanet.subscription.line'].search([('sale_order_id', '=', so.id)])
                if len(subscription_line) == 1:
                    return subscription_line

            # Si rien on retourne un modèle vide
            return self.env['horanet.subscription.line']

    def get_printable_package_line(self, invoice_line):
        """
        Get a package line from an invoice line.

        If there are none or more than one, returns nothing

        :param invoice_line: the invoice line
        :return: the package line
        """
        if invoice_line:
            sols = self.env['sale.order.line'].search([('invoice_lines', 'in', invoice_line.id)])
            pls = self.env['horanet.package.line'].search([('package_order_line_ids', 'in', sols.ids)])

            if len(pls) == 1:
                return pls

            # Si rien on retourne un modèle vide
            return self.env['horanet.package.line']

    def get_printable_invoice_lines(self):
        """Merge invoice lines of same subscription line / product / price_unit."""
        printable_invoice_lines = []

        for sl in self.invoice_line_ids:
            period_line = self.get_printable_package_line(sl) or self.get_subscription_line(sl)
            name = sl.product_id.name
            quantity = sl.quantity
            price_unit = sl.price_unit
            price_subtotal = sl.price_subtotal

            existing = False
            for pil in printable_invoice_lines:
                if not existing and \
                        pil['period_line'] == period_line and \
                        pil['name'] == name and \
                        pil['price_unit'] == price_unit:
                    pil.update({'quantity': pil['quantity'] + quantity})
                    pil.update({'price_subtotal': pil['price_subtotal'] + price_subtotal})
                    existing = True

            if not existing:
                printable_invoice_lines += [{
                    'period_line': period_line,
                    'name': name,
                    'quantity': quantity,
                    'price_unit': price_unit,
                    'price_subtotal': price_subtotal,
                }]

        return printable_invoice_lines

    def get_key_one(self):
        """
        Compute the first key of the sepa.

        :return: first key of sepa
        """
        i = 0
        p = 0
        amount_str = str(format(self.amount_total, '.2f')).replace('.', '')
        str_size = len(amount_str)
        for u in amount_str:
            p += int(u) * (str_size - i)
            i += 1

        result = str(p + 131)[1:]
        return result

    def get_roldeb(self):
        """
        Compute a second key of the sepa.

        :return: second key of sepa
        """
        id_size = len(str(self.id))
        result = str(self.id)
        comp = 15 - id_size
        for u in range(0, comp, 1):
            result = "0" + result
        return result

    def get_key_two(self):
        """
        Compute the second key of the sepa.

        :return: second key of sepa
        """
        i = 0
        p = 0
        rol_deb = self.get_roldeb()
        id_post = self.company_id.ormc_id_post
        code = '23' + str(rol_deb) + str(id_post) + '49'
        str_size = len(code)
        for u in code:
            p += int(u) * (str_size - i)
            i += 1

        result = str(p)[1:]
        return result

    def get_formule_code(self):
        u"""
        Calcul du code formule.

        Le n° de formule ou code formule contient (de droite à gauche) :
          o le millésime sur 2 caractères
          o le code budget ou 00
          o le code produit converti sur 3 caractères.
          o le code période sur 1 caractère
          o le code budget
        """
        code_periode_1_car = self.env.ref('horanet_demat_ormc_psv2.pes_attrs_sr_per').value
        code = ''.join([
            self.company_id.ormc_cod_col,
            code_periode_1_car,
            self.get_numeric_product_code(),
            self.batch_id.campaign_id.budget_code_id.ormc_cod_bud or '00',
            str(self.get_accounting_year() % 100).zfill(2)

        ])
        return code

    def get_accounting_year(self):
        if self.batch_id and self.batch_id.role_ids:
            accounting_year = self.batch_id.role_ids[0].fiscal_year.accounting_year
        else:
            date = self.date_due or fields.Date.today()
            accounting_year = int(date[0:4])

        return accounting_year

    def get_numeric_product_code(self):
        cod_prod = self.get_product_code()
        return str((ord(cod_prod[0]) - 65) * 26 + (ord(cod_prod[1]) - 64)).zfill(3)

    def get_key_five(self):
        u"""
        Calcul de la clé 5.

        Le calcul de la clé 5 est fonction du résultat de:
        11 - (reste de la division du n° de formule/11).

        Si le résultat est 10 alors 0.
        Si le résultat est 11 alors 1.
        :return:
        """
        formule_code = int(self.get_formule_code())
        key = 11 - (formule_code % 11)
        if key >= 10:
            key -= 10
        return key

    def get_split_bank_account(self):
        """
        Compute splitted bank account.

        ex : FR7630001007941234567890185 => FR76 3000 1007 9412 3456 7890 185

        :return: splitted bank account
        """
        return ' '.join(re.findall('....?', self.subscription_id.bank_account_id.acc_number))

    @api.depends('subscription_id', 'batch_id')
    def _compute_mandate_id(self):
        u"""Surcharge de la méthode du module account_mass_invoicing pour créer les mandat de prélèvement one-off."""
        for rec in self:

            if rec.subscription_id.payment_mode.bank_account_required:
                rec.mandate_id = rec.subscription_id.banking_mandate or False
            elif rec.batch_id and rec.batch_id.role_ids:
                rum = "TIPSEPA" + rec.company_id.ormc_id_post + rec.company_id.ormc_cod_col \
                      + rec.batch_id.campaign_id.budget_code_id.ormc_cod_bud \
                      + rec.get_roldeb() \
                      + str(rec.batch_id.role_ids[0].fiscal_year.accounting_year)[2:]

                # On cherche le mandat avec cette référence, sinon on le crée
                rec.mandate_id = self.env['account.banking.mandate'].search([
                    ('unique_mandate_reference', '=', rum)
                ]) or self.env['account.banking.mandate'].create({
                    'type': 'oneoff',
                    'unique_mandate_reference': rum
                })
            else:
                rec.mandate_id = False
