# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.tools import safe_eval


class DepositPointSetUpPartner(models.TransientModel):
    u"""Wizard assistant de création de partner environnement."""

    # region Private attributes
    _inherit = 'partner.setup.wizard'

    # endregion

    # region Default methods
    def _get_default_mapping_pav(self):
        return safe_eval(self.env['ir.config_parameter'].get_param(
            'partner_contact_identification.default_deposit_point_mapping_id', 'False'
        ))
    # endregion

    # region Fields declaration
    deposit_point_mapping_id = fields.Many2one(
        string="Mapping",
        comodel_name='partner.contact.identification.mapping',
        default=lambda self: self._get_default_mapping_pav(),
        domain="[('mapping', '=', 'csn')]",
        readonly=True
    )
    deposit_point_max_length = fields.Integer(related='deposit_point_mapping_id.max_length', readonly=True)
    deposit_point_mapping = fields.Selection(related='deposit_point_mapping_id.mapping', readonly=True)
    deposit_point_csn_number = fields.Char(string="CSN Number")
    deposit_point_tag_id = fields.Many2one(
        string='Tag',
        comodel_name='partner.contact.identification.tag',
        domain="[('is_assigned', '=', False),"
               " ('number', '=?', deposit_point_csn_number),"
               " ('mapping_id', '=', deposit_point_mapping_id),"
               "]",
    )
    # endregion

    # region Fields method
    @api.onchange('deposit_point_mapping_id', 'deposit_point_csn_number')
    def _onchange_deposit_point_medium_infos(self):
        self.possible_deposit_point_tag_ids = self.env['partner.contact.identification.tag'].search([
            ('is_assigned', '=', False),
            ('number', '=', self.deposit_point_csn_number),
            ('mapping_id', '=', self.deposit_point_mapping_id.id),
        ])
        if len(self.possible_deposit_point_tag_ids) == 1:
            self.deposit_point_tag_id = self.possible_deposit_point_tag_ids[0]
        else:
            self.deposit_point_tag_id = False
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_next_stage(self):
        self.ensure_one()

        if self.env.context.get('current_stage') == self.env.ref(
                'environment_waste_collect.wizard_stage_support_attribution').id:
            self.deposit_point_csn_number = False
            self.deposit_point_tag_id = False

        return super(DepositPointSetUpPartner, self).action_next_stage()
    # endregion

    # region Model methods
    # endregion

    pass
