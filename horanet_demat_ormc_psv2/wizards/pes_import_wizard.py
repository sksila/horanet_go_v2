# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ImportWizard(models.TransientModel):
    # region Private attributes
    _name = 'pes.import.wizard'
    _description = "Import PSV2 Wizard"
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    file_import = fields.Binary(string="File")
    file_title = fields.Char(string="Filename")

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
    @api.multi
    def check_validity_psv2_import(self):
        # Vérification de la validité avant import
        return True

    @api.multi
    def import_psv2(self):
        # Vérification de la validité avant import
        return True

    # endregion
