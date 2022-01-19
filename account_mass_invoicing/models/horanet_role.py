# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

STATES_ROLES = [('new', 'New'), ('locked', 'Locked')]


class HoranetRole(models.Model):
    """This model represent accounting roles."""

    # region Private attributes
    _name = 'horanet.role'
    _sql_constraints = [('unicity_on_batch', 'CHECK(1=1)', _("A batch cannot be in multiple roles")),
                        ('unicity_on_number', 'UNIQUE(number,fiscal_year)',
                         _("A role with the same number exists for this fiscal year")),
                        ('unicity_on_recipe_title', 'UNIQUE(recipe_title)',
                         _("A role with this recipe title already exists"))
                        ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name",
        compute='_compute_name',
        readonly=True,
    )

    state = fields.Selection(
        string="State",
        selection=STATES_ROLES,
        default='new'
    )

    number = fields.Integer(
        string="Number",
    )

    recipe_title = fields.Integer(
        string="Recipe title",
    )

    batch_id = fields.Many2one(
        string="Invoice batch",
        comodel_name='horanet.invoice.batch',
        required=True,
        domain="[('state', '!=', 'to_generate')]",
        order='id desc'
    )

    fiscal_year = fields.Many2one(
        string="Fiscal year",
        comodel_name='horanet.accounting.date.range',
        required=True,
    )

    # endregion

    # region Fields method
    @api.depends('fiscal_year', 'fiscal_year.accounting_year', 'number')
    def _compute_name(self):
        for rec in self:
            rec.name = "{} - {} - {}".format(rec.fiscal_year.accounting_year, rec.number, rec.batch_id.name)
    # endregion

    # region Constrains and Onchange
    @api.onchange('fiscal_year')
    def _onchange_role_fiscal_year(self):
        for rec in self:
            if rec.fiscal_year:
                fiscal_year_roles = self.search([('fiscal_year', '=', rec.fiscal_year.id)], order="number desc")
                rec.number = max(len(fiscal_year_roles) + 1, fiscal_year_roles and fiscal_year_roles[0].number + 1 or 0)

    @api.constrains('state')
    def _lock_batch(self):
        """Lock batch if state is in locked."""
        if self.state == 'locked' and self.batch_id.state != 'locked':
            self.batch_id.write({'state': 'locked'})
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_change_state_role(self):
        self.ensure_one()
        # Triggers the lock of the batch, and so the validation of the invoices
        self.state = 'locked'
    # endregion

    # region Model methods
    # endregion

    pass
