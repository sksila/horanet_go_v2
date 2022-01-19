# -*- coding: utf-8 -*-

from odoo import models, fields


class PesRefValueConstraint(models.Model):
    # region Private attributes
    _name = 'pes.referential.value.constraint'
    _description = 'Referential Value Constraint'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    ref_value_1_id = fields.Many2one(string="Referential value 1", comodel_name='pes.referential.value')
    ref_value_2_id = fields.Many2one(string="Referential value 2", comodel_name='pes.referential.value')
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
    # endregion
