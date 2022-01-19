# coding: utf-8

from odoo import fields, models, api


class PartnerCloseContract(models.TransientModel):
    _inherit = 'partner.wizard.close.contract'

    def _get_default_move(self):
        partner = self.partner_id.browse(self.env.context.get('default_partner_id'))

        moves = partner.partner_move_ids.filtered('is_active')

        if moves:
            return moves[0]

    def _get_default_tag(self):
        u"""Surcharge pour chercher un identifiant rattaché à un emménagement."""
        partner = self.partner_id.browse(self.env.context.get('default_partner_id'))

        tags = partner.tag_ids + partner.move_assignation_ids.filtered('is_active').mapped('tag_id')

        if tags:
            return tags[0]

    has_active_moves = fields.Boolean(compute='_compute_has_active_moves')
    move_id = fields.Many2one(
        string="Move",
        comodel_name='partner.move',
        default=_get_default_move,
        domain="[('partner_id', '=', partner_id), ('is_active', '=', True)]"
    )
    move_end_date = fields.Datetime(default=fields.Datetime.now)

    @api.depends('partner_id')
    def _compute_has_active_moves(self):
        for rec in self:
            if self.partner_id.partner_move_ids.filtered('is_active'):
                rec.has_active_moves = True

    @api.depends('partner_id')
    def _compute_has_active_tags(self):
        u"""Surcharge pour prendre les identifiants rattachés aux emménagements de l'usager."""
        for rec in self:
            if self.partner_id.tag_ids or self.partner_id.move_assignation_ids.filtered('is_active').mapped('tag_id'):
                rec.has_active_tags = True

    @api.onchange('partner_id')
    def _onchange_partner(self):
        return {
            'domain': {
                'tag_id': [('id', 'in', self.partner_id.tag_ids.ids +
                            self.partner_id.move_assignation_ids.filtered('is_active').mapped('tag_id').ids)]
            }
        }

    @api.multi
    def action_end_move(self):
        self.ensure_one()

        self.move_id.end_date = self.move_end_date

        return self._refresh_wizard()

    @api.depends('has_active_moves')
    def _compute_hide_subscription_block(self):
        super(PartnerCloseContract, self)._compute_hide_subscription_block()

        for rec in self:
            if rec.has_active_moves:
                rec.hide_subscription_block = True
