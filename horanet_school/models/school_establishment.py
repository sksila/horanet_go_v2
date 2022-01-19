# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HoranetSchoolEstablisment(models.Model):
    # region Private attributes
    _name = 'horanet.school.establishment'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name')
    code = fields.Char(string='Code', size=32, required=True)

    city_id = fields.Many2one(string='City', comodel_name='res.city')
    school_sector_ids = fields.Many2many(string='Sectors', comodel_name='horanet.school.sector',
                                         relation='horanet_school_establishment_school_sector_rel')
    is_public = fields.Boolean(string='Is a public establishment', default=True)
    computed_school_cycle = fields.Many2many(
        string='List of school cycles',
        comodel_name='horanet.school.cycle',
        compute='_compute_school_cycles',
        search='_search_school_cycles'
    )
    school_grade_ids = fields.Many2many(string='List of school grades', comodel_name='horanet.school.grade',
                                        relation='horanet_establishment_grade_rel',
                                        column1='establishment_id',
                                        column2='grade_id', )
    contact_ids = fields.Many2many(string='Contact list', comodel_name='res.partner')

    # endregion

    # region Fields method
    @api.depends('school_grade_ids')
    def _compute_school_cycles(self):
        """Get the distinct school cycles of the school grades."""
        for rec in self:
            rec.computed_school_cycle = rec.school_grade_ids.mapped('school_cycle_id')

    @api.model
    def _search_school_cycles(self, operator, value):
        search_domain = []
        grades_ids = []
        cycles_ids = []
        if operator in ['=', '!=', 'in', 'not in'] and value:
            cycles_ids = self.computed_school_cycle.search([('id', operator, value)]).ids
        elif operator in ['=like', '=ilike', 'like', 'not like', 'ilike', 'not ilike'] and value:
            cycles_ids = self.computed_school_cycle.search([('name', operator, value)]).ids

        if cycles_ids:
            grades_ids = self.school_grade_ids.search([('school_cycle_id', 'in', cycles_ids)]).ids

        search_domain = [('school_grade_ids', 'in', grades_ids)]
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
