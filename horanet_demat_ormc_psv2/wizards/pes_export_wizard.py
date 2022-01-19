# coding: utf-8

import base64
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

reload(sys)
sys.setdefaultencoding('utf8')


class ExportWizard(models.TransientModel):
    # region Private attributes
    _name = "pes.export.wizard"
    _description = "Export PSV2 Wizard"
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    pes_domain_id = fields.Many2one(string="PES Domain", comodel_name='pes.domain', required=True)
    date_declaration = fields.Date(string="Date declaration", required=True)
    domain_code = fields.Char(string="domain code", related="pes_domain_id.code")
    pes_file_id = fields.Many2one(string="PES File", comodel_name='pes.file')
    invoice_ids = fields.Many2many(string="Invoices", comodel_name='account.invoice', store=True)
    invoice_ids_count = fields.Integer(string="Number of invoices", compute='_compute_invoice_ids_count')
    filename = fields.Char(string="File Name", readonly=True)
    data = fields.Binary(string="File")
    state = fields.Selection(string="State", selection=[('step1', 'step1'), ('step2', 'step2')], default='step1')
    error = fields.Char(string="Errors")
    pes_declaration_id = fields.Many2one(string="PES declaration", comodel_name='pes.declaration')
    role_id = fields.Many2one(string='Role', comodel_name='horanet.role')
    last_id_pce = fields.Integer()
    company_id = fields.Many2one(
        string="Company",
        comodel_name='res.company',
        compute='_compute_company_id',
        store=True,
        readonly=True)

    # endregion

    # region Fields method
    @api.depends('invoice_ids')
    def _compute_invoice_ids_count(self):
        for rec in self:
            rec.invoice_ids_count = len(rec.invoice_ids)

    @api.depends('role_id')
    def _compute_company_id(self):
        for obj in self.filtered('role_id'):
            obj.company_id = obj.role_id.fiscal_year.company_id

    # endregion

    # region Constraints and Onchange
    @api.onchange('role_id', 'date_declaration')
    def _compute_invoice_ids(self):
        for obj in self.filtered('role_id'):
            if obj.date_declaration:
                obj.invoice_ids = self.env['account.move.line'].search([
                    ('date_maturity', '>=', self.date_declaration),
                    ('debit', '>', 0.0),
                    ('invoice_id', 'in', obj.role_id.batch_id.invoice_ids.ids),
                    ('invoice_id.state', '=', 'open'),
                ]).filtered(lambda aml: aml.get_ormc_debit() > 0.0).mapped('invoice_id').ids

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_export_psv2(self):
        if not self.pes_declaration_id:
            self.pes_declaration_id = self.env['pes.declaration'].create({
                'pes_domain_id': self.pes_domain_id.id,
                'date_declaration': self.date_declaration,
                'role_id': self.role_id.id,
            })

        # On recalcule le champ calculé car on vient d'un NewId
        self._compute_invoice_ids()

        if not self.invoice_ids:
            raise ValidationError(_("No invoice to export."))

        self.getXML_Body()
        self.env['pes.declaration.file'].create({
            'name': self.filename,
            'pes_declaration_id': self.pes_declaration_id.id,
            'filename': self.filename,
            'data': self.data
        })
        return self._get_self_action_widow()

    @api.multi
    def _get_self_action_widow(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pes.export.wizard',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    # endregion

    # region Model methods
    # endregion

    # region Methodes retournant des valeurs pour lmes attributs
    @api.multi
    def get_emetteur(self):
        for obj in self:
            # company = obj.company_id
            if obj.pes_file_id.file_type_id.name == "PES_Aller":
                # TODO: USE CONFIG
                return 'Horanet'

    @api.multi
    def get_emetteur_adresse(self):
        horanet_go_version = self.env['ir.module.module'].search([('name', '=', 'horanet_go')]).installed_version
        return "Horanet GO v{version}".format(version=horanet_go_version)

    @api.multi
    def get_recepteur(self):
        for obj in self:
            company = obj.company_id
            if obj.pes_file_id.file_type_id.name != "PES_Aller":
                return company.partner_id.name
            else:
                # TODO: USE CONFIG
                return 'CENTRE DES FINANCES PUBLIQUES'
                # return company.helios_partner_id.name

    # endregion

    @api.multi
    def get_date_jour(self):
        return time.strftime('%Y-%m-%d', time.localtime())

    def get_exercice(self):
        return fields.Date.from_string(
            self.role_id.fiscal_year.start_date).year

    def get_nbr_pieces(self):
        return len(self.invoice_ids)

    def get_date_emission_bordereau(self):
        self.ensure_one()

        return fields.Date.today()

    def get_object(self):
        u"""
        Calcul de l'objet du rôle.

        L'objet du rôle correspond à un code produit. Toutes les prestations et les produits de la campagne à l'origine
        du lot du rôle étant censés avoir le même code produit, on prend le code produit de la première facture.
        """
        self.ensure_one()

        return self.invoice_ids and self.invoice_ids[0].get_product_code()

    def _compute_total_untaxed_amount(self):
        total_untaxed_amount = 0
        for invoice in self.invoice_ids:
            total_untaxed_amount += invoice.account_move_line_ids.filtered(
                lambda aml: aml.date_maturity >= self.date_declaration and aml.debit > 0.0
            ).sorted('date_maturity')[0].get_ormc_debit()

        return total_untaxed_amount

    def get_id_pce(self):
        self.last_id_pce = self.last_id_pce and self.last_id_pce + 1 or 1
        return abs(self.last_id_pce / 2)

    @api.multi
    def get_file_name(self):
        seq = self.env['ir.sequence'].next_by_code('pes.file')
        # type_fic = self.pes_file_id.file_type_id.code
        today_date = date.today().strftime("%Y%m%d")
        file_name = "PES_ALLER_%s%s" % (today_date, seq)
        self.write({'filename': file_name + ".xml"})
        return file_name

    def annotate_with_XMLNS_prefixes(self, tree, xmlns_prefix, skip_root_node=True):
        if not ET.iselement(tree):
            tree = tree.getroot()
        iterator = tree.iter()
        if skip_root_node:  # Add XMLNS prefix also to the root node?
            iterator.next()
        for e in iterator:
            if ':' not in e.tag:
                e.tag = xmlns_prefix + ":" + e.tag

    def add_XMLNS_attributes(self, tree, xmlns_uris_dict):
        if not ET.iselement(tree):
            tree = tree.getroot()
        for prefix, uri in xmlns_uris_dict.items():
            tree.attrib['xmlns:' + prefix] = uri

    def add_simple_attributes(self, element, xmlns_uris_dict):
        for prefix, uri in xmlns_uris_dict.items():
            element.attrib[prefix] = uri

    def get_attributes_by_type(self, root_bloc_obj, type, obj=False):
        attrs = {}
        for attr in root_bloc_obj.attrs_ids:
            if attr.attrs_type == type:
                attr_value = str(self.get_object_value_for_attrs(obj, attr, "attribute"))
                # print "attr_value : ",attr_value
                if attr_value:
                    attrs.update({attr.code: attr_value})
        return attrs

    def get_obj_from_element(self, element, parent_obj=False):
        if element.pes_input_object_id.code == "pes_file":
            return self
        elif element.pes_input_object_id.code == "account_invoice":
            return parent_obj.invoice_ids

        elif element.pes_input_object_id.code == "account_invoice_line":
            return parent_obj.invoice_line_ids

        elif element.pes_input_object_id.code == "account_move_line":
            line_ids = parent_obj.account_move_line_ids.filtered(
                lambda aml: aml.date_maturity >= self.date_declaration and aml.debit > 0.0).sorted('date_maturity')
            return line_ids and line_ids[0]
        else:
            return parent_obj

    def verify_element_validity(self, element, obj):
        if element.attrs_ids:
            for attr in element.attrs_ids:
                if attr.attrs_type == "simple":
                    attr_value = str(self.get_object_value_for_attrs(obj, attr, "attribute"))
                    if attr_value == "False":
                        if element.is_required:
                            error = self.error + " -Valeur introuvable : " + attr.value
                            self.error = error
                            self.env['pes.message'].post_message(
                                "Erreur d'accès à l'attribut %s. Veuillez vérifier la valeur %s !" % (
                                    attr.code, attr.value),
                                'error', 'pes_aller', 'Export', self.pes_declaration_id)
                        else:
                            self.env['pes.message'].post_message(
                                "Erreur d'accès à l'attribut %s. Veuillez vérifier la valeur %s !" % (
                                    attr.code, attr.value),
                                'warning', 'pes_aller', 'Export', self.pes_declaration_id)
                        return False
        return True

    def add_subelement(self, parent_node, children_bloc_ids, conditionnal_attr_id, parent_obj=False):
        if children_bloc_ids:
            for element in children_bloc_ids:

                object = self.get_obj_from_element(element, parent_obj)

                for obj in object:
                    bloc_to_add = True
                    if element.conditionnal_attr_id:
                        conditionnal_attr_value = \
                            self.get_object_value_for_attrs(obj, element.conditionnal_attr_id, "attribute")
                        if not conditionnal_attr_value:
                            bloc_to_add = False

                    if bloc_to_add and self.verify_element_validity(element, obj):
                        child_node = ET.SubElement(parent_node, element.code)
                        root_node_xmlns = self.get_attributes_by_type(element, 'simple', obj)
                        if root_node_xmlns:
                            self.annotate_with_XMLNS_prefixes(child_node, element.namespace_id.code)
                            self.add_simple_attributes(child_node, root_node_xmlns)
                        if element.element_value_type == "element":
                            if element.children_bloc_ids:
                                self.add_subelement(
                                    child_node, element.children_bloc_ids, element.conditionnal_attr_id, obj)
                        elif element.element_value_type == "text":
                            child_node.text = str(self.get_object_value_for_attrs(obj, element, "element"))

    @api.multi
    def getXML_Body(self):
        self.error = ""
        root_bloc_obj = self.pes_file_id.struct_fichier_id
        root_node = ET.Element(root_bloc_obj.code)
        root_node_xmlns = self.get_attributes_by_type(root_bloc_obj, 'namespace')
        self.annotate_with_XMLNS_prefixes(root_node, root_bloc_obj.namespace_id.code, False)
        self.add_XMLNS_attributes(root_node, root_node_xmlns)
        self.add_subelement(root_node, root_bloc_obj.children_bloc_ids, root_bloc_obj.conditionnal_attr_id)
        if self.error:
            raise UserError(
                _('Les erreurs suivantes doivent être corrigées avant de pouvoir '
                  'Générer le fichier XML : %s !') % self.error)

        file_content = ET.tostring(root_node, method='xml')
        file_content = '<?xml version="1.0" encoding="ISO-8859-1"?>' + file_content

        self.write({'state': 'step2', 'data': base64.encodestring(file_content)})

    @api.multi
    def _search_value_from_reference(self, value, ref):
        result = self.env['pes.referential.value'].search(
            [('id', 'in', ref.ref_value_ids.ids),
             ('name', '=', value)],
            limit=1
        ).value
        if result:
            return result
        else:
            return ref.default_value

    def get_object_value_for_attrs(self, obj, attr, type=False):
        value = attr.value
        if obj and attr.field_type == "field":
            value = eval('obj.' + attr.value)

        elif obj and attr.field_type == "function":
            if value in ['get_cle1', 'get_cle2']:
                value = eval('obj.%s(cod_col=%s, exer=%s)' % (
                    attr.value,
                    self.role_id.fiscal_year.company_id.ormc_cod_col,
                    self.get_exercice())
                             )
            else:
                value = eval("obj.%s()" % (attr.value))

        elif type == "attribute":
            if attr.value_type == "reference":
                return self._search_value_from_reference(value, attr.reference_id)

        return value

    @api.multi
    def check_validity_psv2_export(self):
        # Vérification de la validité avant export
        return True
