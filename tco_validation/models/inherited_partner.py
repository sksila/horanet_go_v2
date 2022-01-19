# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

WORKFLOW_SELECTION = [
    ('initial', 'Initial'),
    ('pending', 'Pending'),
    ('validated', 'Validated'),
    ('rejected', 'Rejected')
]


class ResPartner(models.Model):
    """Inherit res.partner to add fields."""

    # region Private attributes
    _inherit = 'res.partner'

    # endregion

    # region Default methods
    def _get_default_workflow_value(self):
        """Set the default workflow value.

        :return: 'initial'
        """
        return 'initial'

    # endregion

    # region Fields declaration
    address_workflow = fields.Selection(
        string="Address workflow state",
        selection=WORKFLOW_SELECTION,
        compute='_compute_address_workflow',
        default=_get_default_workflow_value,
        store=True
    )
    is_address_valid = fields.Boolean(
        string="Address valid",
        compute='_compute_is_address_valid',
        search='_search_is_address_valid'
    )

    garant_workflow = fields.Selection(
        string="Garant relation workflow state",
        selection=WORKFLOW_SELECTION,
        compute='_compute_garant_workflow',
        default=_get_default_workflow_value,
        store=True
    )
    is_garant_valid = fields.Boolean(
        string="Garant valid",
        compute='_compute_is_garant_valid',
        search='_search_is_garant_valid'
    )

    # endregion

    # region Fields method
    @api.multi
    @api.depends('address_status')
    def _compute_address_workflow(self):
        """Reset the address workflow if the address change except for admin."""
        for rec in self:
            if rec.id == self.env.ref('base.partner_root').id:
                rec.address_workflow = 'validated'
            elif self.env.context.get('creation_mode'):
                rec.address_workflow = 'initial'
            else:
                rec.address_workflow = 'pending'

    @api.multi
    @api.depends('garant_ids')
    def _compute_garant_workflow(self):
        """Reset the relations workflow if garants change except for admin."""
        for rec in self:
            if rec.id == self.env.ref('base.partner_root').id:
                rec.garant_workflow = 'validated'
            elif self.env.context.get('creation_mode'):
                rec.garant_workflow = 'initial'
            else:
                rec.garant_workflow = 'pending'

    @api.multi
    @api.depends('address_workflow')
    def _compute_is_address_valid(self):
        """Check if the address is valid depending on the workflow."""
        for rec in self:
            is_address_valid = False
            if rec.address_workflow == 'validated' \
                    and rec.address_status in ['to_confirm', 'confirmed']:
                is_address_valid = True

            rec.is_address_valid = is_address_valid

    @api.multi
    @api.depends('garant_workflow')
    def _compute_is_garant_valid(self):
        """Check if the relations are valid depending on the workflow."""
        for rec in self:
            is_garant_valid = False

            if rec.garant_workflow == 'validated' \
                    or rec.garant_workflow == 'initial' and not rec.garant_ids:
                is_garant_valid = True

            rec.is_garant_valid = is_garant_valid

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """Add key in the context to be able to know if we are in creation mode.

        when computing the address and garant workflow
        """
        context = self.env.context.copy()
        context['creation_mode'] = True
        self.env.context = context

        return super(ResPartner, self).create(vals)

    # endregion

    # region Actions
    @api.multi
    def action_workflow_validate_address(self):
        """Validate the address workflow."""
        for rec in self:
            rec.address_workflow = 'validated'

    @api.multi
    def action_workflow_reject_address(self):
        """Reject the address workflow."""
        for rec in self:
            rec.address_workflow = 'rejected'

    @api.multi
    def action_workflow_validate_relations(self):
        """Validate the relations workflow."""
        for rec in self:
            rec.garant_workflow = 'validated'

    @api.multi
    def action_workflow_reject_relations(self):
        """Reject the relations workflow."""
        for rec in self:
            rec.garant_workflow = 'rejected'

    # endregion

    # region Model methods
    @api.model
    def _search_is_address_valid(self, operator, value):
        search_domain = []
        if operator == '=' and value is True or operator == '!=' and value is False:
            search_domain = [('address_workflow', '=', 'validated')]
        elif operator == '=' and value is False or operator == '!=' and value is True:
            search_domain = ['!', ('address_workflow', '=', 'validated')]
        return search_domain

    @api.model
    def _search_is_garant_valid(self, operator, value):
        search_domain = []
        if operator == '=' and value is True or operator == '!=' and value is False:
            search_domain = [
                '|', '&',
                ('garant_workflow', 'in', ['initial', 'validated']),
                ('garant_ids', '=', False),
                ('garant_workflow', '=', 'validated'),
            ]
        elif operator == '=' and value is False or operator == '!=' and value is True:
            search_domain = [
                '!', '|', '&',
                ('garant_workflow', 'in', ['initial', 'validated']),
                ('garant_ids', '=', False),
                ('garant_workflow', '=', 'validated'),
            ]
        return search_domain

    # endregion

    pass
