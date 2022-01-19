# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields

_logger = logging.getLogger(__name__)


class HoranetSchoolGrade(models.Model):
    # region Private attributes
    _name = 'horanet.school.grade'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)

    school_cycle_id = fields.Many2one(string='School Cycle', comodel_name='horanet.school.cycle')
    school_establishment_ids = fields.Many2many(
        string='List of school grades',
        comodel_name='horanet.school.establishment',
        relation='horanet_establishment_grade_rel',
        column2='establishment_id',
        column1='grade_id', )
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
