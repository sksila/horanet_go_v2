# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HoranetSchoolCycle(models.Model):
    # region Private attributes
    _name = 'horanet.school.cycle'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)
    school_grade_ids = fields.One2many(
        string='School grades',
        comodel_name='horanet.school.grade',
        inverse_name='school_cycle_id')
    computed_establishment_ids = fields.Many2many(
        string='List of school establishment', store=False,
        comodel_name='horanet.school.establishment',
        compute='_compute_school_establishment',
        search='_search_school_establishment'
    )

    # endregion

    # region Fields method
    @api.depends('school_grade_ids')
    def _compute_school_establishment(self):
        """Get the school establishment ids by the school grades."""
        for rec in self:
            rec.computed_establishment_ids = rec.school_grade_ids.mapped('school_establishment_ids.id')

    @api.model
    def _search_school_establishment(self, operator, value):
        search_domain = []
        if (operator == '=' and value) or (operator == '!=' and not value):
            cycle_ids = self.env['horanet.school.establishment'].search([('school_grade_ids', '!=', None)]).mapped(
                'school_grade_ids.school_cycle_id.id')
            search_domain = [('id', 'in', cycle_ids)]
        elif (operator == '=' and not value) or (operator == '!=' and value):
            cycle_ids = self.env['horanet.school.establishment'].search([('school_grade_ids', '!=', None)]).mapped(
                'school_grade_ids.school_cycle_id.id')
            search_domain = [('id', 'in', cycle_ids)]
        elif operator in ['in', 'not in'] and isinstance(value, (list, tuple)):
            value = [x for x in value if x]
            cycle_ids = self.env['horanet.school.establishment'].search([('id', 'in', value)]).mapped(
                'school_grade_ids.school_cycle_id.id')
            if operator == 'in':
                search_domain = [('id', value and 'in' or 'not in', cycle_ids)]
            else:
                search_domain = [('id', value and 'not in' or 'in', cycle_ids)]
        return search_domain

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
