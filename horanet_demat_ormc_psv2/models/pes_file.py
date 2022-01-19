# -*- coding: utf-8 -*-

from odoo import models, fields


class PesFile(models.Model):
    # region Private attributes
    _name = 'pes.file'
    _description = 'File Architecture'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True, )
    description = fields.Char(string="Description")
    file_type_id = fields.Many2one(string="File Type", comodel_name='pes.file.type')
    struct_fichier_id = fields.Many2one(string="File Structure", comodel_name='pes.bloc')
    pes_domain_id = fields.Many2one(string="Domain", comodel_name='pes.domain')
    version = fields.Char(string="Version", default="2")
    is_actif = fields.Boolean(string="Etat fichier")
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
