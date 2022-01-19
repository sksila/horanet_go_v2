# -*- coding: utf-8 -*-

from odoo import models, fields


class PesDeclarationFile(models.Model):
    # region Private attributes
    _name = "pes.declaration.file"
    _description = "PSV2 Declaration File"
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name")
    pes_domain_id = fields.Many2one(string="PES Domain", comodel_name='pes.domain')
    pes_declaration_id = fields.Many2one(string="Declaration", comodel_name='pes.declaration')
    filename = fields.Char(string="File Name", readonly=True)
    data = fields.Binary(string="File", attachment=True)
    error_ids = fields.One2many(string="Errors", comodel_name='pes.message', inverse_name='declaration_file_id')
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
