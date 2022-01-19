# -*- coding: utf-8 -*-

from odoo import models, fields


class PesRef(models.Model):
    # region Private attributes
    _name = 'pes.referential'
    _description = 'Referential'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")
    default_value = fields.Char(string="Default value")
    ref_value_ids = fields.One2many(string="Values", comodel_name='pes.referential.value', inverse_name='ref_id')
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
