# -*- coding: utf-8 -*-

from odoo import models, fields


class PesRefValue(models.Model):
    # region Private attributes
    _name = 'pes.referential.value'
    _description = 'Referential Value'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Value src")
    description = fields.Char(string="Description")
    value = fields.Char(string="Value ref")
    ref_id = fields.Many2one(string="Referential", comodel_name='pes.referential')
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
