# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, _


_logger = logging.getLogger(__name__)


class HoranetBudgetCode(models.Model):

    # region Private attributes
    _name = 'horanet.budget.code'
    _inherit = ['application.type']
    _rec_name = 'budget_code'
    _sql_constraints = [('unicity_on_budget_code_and_application_type', 'UNIQUE(budget_code,application_type)',
                         _('The budget code cannot be twice on the same application type'))]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    budget_code = fields.Char(string="Budget code", required=True)
    company_id = fields.Many2one(string="Company id", comodel_name='res.company')

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
