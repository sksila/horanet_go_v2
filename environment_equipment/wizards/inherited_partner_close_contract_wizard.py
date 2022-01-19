# coding: utf-8

from odoo import fields, models, api


class PartnerCloseContract(models.TransientModel):

    # region Private attributes
    _inherit = 'partner.wizard.close.contract'

    # endregion

    # region Default methods
    def _get_default_equipment(self):
        partner = self.partner_id.browse(self.env.context.get('default_partner_id'))
        if partner:
            equipments = self.env['maintenance.equipment'].search([
                ('owner_partner_id', '=', partner.id),
                ('category_id.equipment_follows_producer', '=', True)])

            if equipments:
                return equipments[0]

    # endregion

    # region Fields declaration
    has_active_equipments = fields.Boolean(compute='_compute_has_active_equipments')
    equipment_id = fields.Many2one(
        string="Equipment",
        comodel_name='maintenance.equipment',
        default=_get_default_equipment,
        domain="[('owner_partner_id', '=', partner_id),"
               " ('category_id.equipment_follows_producer', '=', True)]"
    )
    allocation_end_date = fields.Datetime(default=fields.Datetime.now)

    # endregion

    # region Fields method
    @api.depends('partner_id')
    def _compute_has_active_equipments(self):
        for rec in self:
            partner = self.partner_id.browse(self.env.context.get('default_partner_id'))
            equipments = False
            if partner:
                equipments = self.env['maintenance.equipment'].search([
                    ('owner_partner_id', '=', partner.id),
                    ('category_id.equipment_follows_producer', '=', True)])

            rec.has_active_equipments = True if equipments else False

    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    @api.depends('has_active_equipments')
    def _compute_hide_subscription_block(self):
        super(PartnerCloseContract, self)._compute_hide_subscription_block()

        for rec in self:
            if rec.has_active_equipments:
                rec.hide_subscription_block = True
    # endregion

    # region Actions
    @api.multi
    def action_deallocate_equipment(self):
        self.ensure_one()

        self.equipment_id.allocation_ids.filtered('is_active').end_date = self.allocation_end_date

        return self._refresh_wizard()
    # endregion

    # region Model methods
    # endregion
