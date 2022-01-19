# -*- coding: utf-8 -*-

from odoo import models, fields


class CenterApplication(models.Model):
    # region Private attributes
    _name = 'pes.application'
    _description = 'Applications'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", size=64, required=True)
    code = fields.Char(string="Code", size=64, required=True)

    sequence = fields.Integer(string="Sequence")
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
