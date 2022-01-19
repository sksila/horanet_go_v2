# -*- coding: utf-8 -*-

from odoo import models, api, fields


class ORMCExportHoranetRole(models.Model):
    """Surcharge du model horanet.role pour y ajouter l'export ORMC."""

    # region Private attributes
    _inherit = 'horanet.role'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    pes_declaration_id = fields.Many2one(
        string='Declaration',
        comodel_name='pes.declaration',
        compute='_compute_pes_declaration_id',
    )
    date_declaration = fields.Date(
        string='Date declaration',
        related='pes_declaration_id.date_declaration',
        readonly='True',
    )
    ormc_pes_file_ids = fields.One2many(
        string='ORMC files',
        related='pes_declaration_id.file_ids',
        readonly='True',
    )

    # endregion

    # region Fields method
    @api.depends()
    def _compute_pes_declaration_id(self):
        for rec in self:
            rec.pes_declaration_id = self.env['pes.declaration'].search([
                ('role_id', '=', rec.id)
            ], order='id desc', limit=1)

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_export(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'PES Generator',
            'view_type': 'form',
            'res_model': 'pes.export.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_role_id': self.id,
                'default_date_declaration': self.date_declaration or fields.Date.today(),
            },
        }

    # endregion

    # region Model methods
    # endregion

    pass
