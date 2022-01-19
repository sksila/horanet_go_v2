# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields

_logger = logging.getLogger(__name__)


class HoranetSchoolClassroom(models.Model):
    # region Private attributes
    _name = 'horanet.school.classroom'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    school_grade_ids = fields.Many2many(string="School grades", comodel_name='horanet.school.grade',
                                        relation='horanet_classroom_grade_rel', )
    teacher_id = fields.Many2one(string="Teacher", comodel_name='res.partner')
    school_establishment_id = fields.Many2one(string='Establishment', comodel_name='horanet.school.establishment')
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
