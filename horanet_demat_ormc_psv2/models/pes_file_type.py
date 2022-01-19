# -*- coding: utf-8 -*-

from odoo import models, fields


class PesFileType(models.Model):
    # region Private attributes
    _name = 'pes.file.type'
    _description = 'File Type'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
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
