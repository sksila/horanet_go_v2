# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PesDeclaration(models.Model):
    # region Private attributes
    _name = 'pes.declaration'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "PSV2 Declaration"

    # endregion

    # region Default methods
    def _get_name_declaration(self):
        seq = self.env['ir.sequence'].next_by_code('pes.declaration')
        return seq

    # endregion

    # region Fields declaration
    state = fields.Selection(
        string="State",
        selection=[
            ('draft', "Draft"),
            ('waiting', u"Posté"),
            ('attente', "En attente de transmission"),
            ('transmis', "Transmis"),
            ('ack', "Ack"),
            ('nack', "Nack"),
            ('traitement', "En traitement"),
            ('information', "Informations disponibles"),
            ('erreur', "Erreur")],
        default='draft',
        track_visibility='onchange',
        index=True)

    name = fields.Char(sting="Name", default=_get_name_declaration)
    pes_domain_id = fields.Many2one(string="PES Domain", comodel_name='pes.domain')
    date_declaration = fields.Date(string="Date declaration")
    file_ids = fields.One2many(
        string="Files",
        comodel_name='pes.declaration.file',
        inverse_name='pes_declaration_id',
        track_visibility='onchange',
        index=True,
    )
    error_ids = fields.One2many(
        string="Errors",
        comodel_name='pes.message',
        inverse_name='pes_declaration_id',
        track_visibility='onchange',
        index=True,
    )
    role_id = fields.Many2one(string="Role", comodel_name='horanet.role')

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_open_import_wizard(self):
        return self._get_action_window(
            "PES Import",
            'pes.import.wizard',
            target='new',
            context={'declaration': self.id})

    @api.multi
    def action_open_export_wizard(self):
        return self._get_action_window(
            "PES Generator",
            'pes.export.wizard',
            target='new',
            context={
                'default_pes_declaration_id': self.id,
                'default_pes_domain_id': self.pes_domain_id.id,
                'default_role_id': self.role_id.id,
                'default_date_declaration': self.date_declaration
            })

    @api.multi
    def action_open_errors(self):
        return self._get_action_window(
            "Errors",
            'pes.message',
            view_mode='tree,form',
            context={"declaration": self.id},
            domain=[('id', 'in', self.error_ids.ids)])

    @api.multi
    def action_open_files(self):
        return self._get_action_window(
            "Files",
            'pes.declaration.file',
            view_mode='tree,form',
            context={"declaration": self.id},
            domain=[('id', 'in', self.file_ids.ids)])

    # endregion

    # region Model methods
    def _get_action_window(self, name, res_model, view_mode='form', target='current', context={}, domain=[]):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'res_model': res_model,
            'view_mode': view_mode,
            'target': target,
            'context': context,
            'domain': domain
        }
    # endregion
