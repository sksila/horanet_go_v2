# -*- coding: utf-8 -*-

from odoo import models, fields


class PesDomain(models.Model):
    # region Private attributes
    _name = 'pes.domain'
    _description = 'PES Domain'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Char(string="Description")
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
