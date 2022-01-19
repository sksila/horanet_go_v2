# -*- coding: utf-8 -*-

import logging
import re

from odoo import models, fields, _, api


_logger = logging.getLogger(__name__)

XPATH_VIEW_ARCH_TEMPLATE = """
    <xpath expr="//container[@name='{}']" position="inside">
        <t t-call='{}'/>
    </xpath>
    """


class ReportSepaDynamicElement(models.Model):
    """
    This class represents elements that we want to add dynamically in invoice report SEPA at <container> positions.

    This elements are templates created by other modules and whose ID begin by 'report_invoice_document_sepa_'.
    """

    # region Private attributes
    _name = 'report.sepa.dynamic.element'
    _sql_constraints = [('unicity_on_view_template_id', 'UNIQUE(view_template_id)',
                         _("You can't add same template twice on invoice report"))]
    _order = 'container, sequence, id'
    # endregion

    # region Default methods
    @api.model
    def _get_containers(self):
        template = self.env.ref('account_invoice_report_sepa.report_invoice_document_sepa')
        containers = re.findall(
            '''(?:<container).*(?:name=")([\w]+)".*(?:string=")([\w '&#;]+)".*>''', template.arch_db)
        return [(container[0], container[1]) for container in containers]

    @api.model
    def _get_domain_view_template_id(self):
        view_ids = self.env['ir.model.data'].search([
            ('model', '=', 'ir.ui.view'),
            ('name', 'ilike', 'report_invoice_document_sepa_'),
        ]).mapped('res_id')
        return [('id', 'in', view_ids)]
    # endregion

    # region Fields declaration
    sequence = fields.Integer(string="Sequence")
    view_template_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string='Element',
        required=True,
        domain=_get_domain_view_template_id,
    )
    container = fields.Selection(string="Container", selection='_get_containers')
    xpath_view_id = fields.Many2one(
        string="Xpath view",
        comodel_name='ir.ui.view',
        readonly=True,
    )
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """Override create to create xpath view."""
        element = super(ReportSepaDynamicElement, self).create(vals)

        # On crée une nouvelle vue avec le xpath
        view_values = {
            'name': _("Inherited report invoice SEPA - Add template {} {}").format(
                element.view_template_id.id, element.container.replace('_', ' ')),
            'type': 'qweb',
            'priority': element.sequence,
            'inherit_id': self.env.ref('account_invoice_report_sepa.report_invoice_document_sepa').id,
            'arch': XPATH_VIEW_ARCH_TEMPLATE.format(
                element.container, element.view_template_id.xml_id),
        }
        element.xpath_view_id = self.env['ir.ui.view'].create(view_values)

        return element

    @api.multi
    def write(self, vals):
        """Override write to modify xpath view."""
        result = super(ReportSepaDynamicElement, self).write(vals)

        # On modifie la vue si un des éléments a changé
        if vals.get('sequence') or vals.get('container') or vals.get('view_template_id'):
            new_view_values = {
                'arch': XPATH_VIEW_ARCH_TEMPLATE.format(
                    self.container, self.view_template_id.xml_id),
                'priority': self.sequence,
            }
            self.xpath_view_id.write(new_view_values)

        return result

    @api.multi
    def unlink(self):
        """Override unlink to unlink xpath view."""
        self.mapped('xpath_view_id').unlink()

        return super(ReportSepaDynamicElement, self).unlink()
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
