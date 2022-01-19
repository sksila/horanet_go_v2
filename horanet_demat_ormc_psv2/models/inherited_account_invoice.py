# -*- coding: utf-8 -*-
import base64
import gzip

from odoo import models


class InheritedAccountInvoice(models.Model):
    # region Private attributes
    _inherit = "account.invoice"

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
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
    def get_invoice_encoded_pdf(self):
        pdf = self.env['report'].sudo().get_pdf([self.id], 'account.report_invoice')
        with gzip.open('/tmp/file.gz', 'wb') as f:
            f.write(pdf)
            f.close()
        with open('/tmp/file.gz', 'rb') as f:
            file_content = f.read()

        return base64.b64encode(file_content)

    def get_pdf_name(self):
        num = self.number.split('/')
        name = self.partner_id.name.replace(" ", "_")
        return "F" + num[2] + "_" + name + ".pdf"

    def get_pdf_invoice_description(self):
        return "Facture " + self.number

    def get_cle1(self, cod_col, exer):
        nat_pce = self.env.ref('horanet_demat_ormc_psv2.pes_attrs_sr_2_2_1_1_3')
        value_nat_pce = self.env['pes.referential.value'].search(
            [('id', 'in', nat_pce.reference_id.ref_value_ids.ids),
             ('name', '=', nat_pce.value)],
            limit=1
        ).value or nat_pce.reference_id.default_value

        exer = str(exer)

        number = int('{cod_col}{nat_pce}{exer}{num_dette}'.format(
            cod_col=cod_col, nat_pce=value_nat_pce, exer=exer[-2:], num_dette=self.id))

        return 11 - (number % 11) if number % 11 > 1 else number % 11

    def get_cle2(self, cod_col, exer):
        per = self.env.ref('horanet_demat_ormc_psv2.pes_attrs_sr_per')
        exer = str(exer)
        number = int('{exer}{per}00{num_dette}'.format(
            exer=exer[-2:], per=per.value, num_dette=self.id))

        return chr((number % 23) + 65)

    def get_code_res_deb(self):
        country = self.partner_id.country_id
        fr_country = self.env.ref('base.fr')

        code_res = 0
        if country != fr_country:
            code_res = 1

        return code_res

    def get_adr2(self):
        return ' '.join([self.partner_id.street_number_id.name, self.partner_id.street_id.name]) \
            if self.partner_id.street_number_id and self.partner_id.street_id \
            else self.partner_id.street

    def get_civilite_to_add(self):
        return self.partner_id.cat_tiers_id.value == '01'

    def get_product_code(self):
        u"""
        Calcul du code produit de la facture.

        Tous les articles facturés au sein d'une facture d'un lot sont censés avoir le même code produit.
        On retourne donc celui de la première ligne de facture
        """
        return self.invoice_line_ids and str(self.invoice_line_ids[0].product_id.cod_prod_loc)
    # endregion
