
from odoo import fields, models, api


class PartnerCloseContract(models.TransientModel):
    """Wizard closing contract."""

    # region Private attributes
    _name = 'partner.wizard.close.contract'

    # endregion

    # region Default methods
    def _get_default_subscription(self):
        """Select a default subscription."""
        context = self.env.context
        subscriptions = self.env['horanet.subscription'].search([('client_id', '=', context.get('default_partner_id')),
                                                                 ('state', '=', 'active'),
                                                                 ('application_type', '=', 'environment')
                                                                 ])
        if subscriptions:
            return subscriptions[0]

    def _get_default_tag(self):
        """Select a default subscription."""
        partner = self.partner_id.browse(self.env.context.get('default_partner_id'))

        tags = partner.tag_ids

        if tags:
            return tags[0]

    # endregion

    # region Fields declaration
    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner', required=True)
    has_active_subscriptions = fields.Boolean(compute='_compute_has_active_subscriptions')
    subscription_id = fields.Many2one(string="Subscription", comodel_name='horanet.subscription',
                                      domain="[('client_id', '=', partner_id) , ('state', '=', 'active'), "
                                             "('application_type', '=', 'environment')]",
                                      default=_get_default_subscription)
    subscription_end_date = fields.Datetime(related='subscription_id.closing_date', readonly=True)
    date_close = fields.Date(string="Date close", default=fields.Date.context_today)
    close_type = fields.Selection(string="Close date",
                                  selection=[('date', 'Chosen date'), ('period', 'End of contract period')],
                                  default='period')
    prorata_temporis = fields.Boolean(string="Apply prorata", default=True)

    has_active_tags = fields.Boolean(compute='_compute_has_active_tags')
    tag_id = fields.Many2one(
        string='Tag',
        comodel_name='partner.contact.identification.tag',
        default=lambda self: self._get_default_tag(),
    )

    hide_subscription_block = fields.Boolean(compute='_compute_hide_subscription_block')
    # endregion

    # region Fields method
    @api.depends('partner_id')
    def _compute_has_active_subscriptions(self):
        for rec in self:
            if self.partner_id.environment_subscription_id:
                rec.has_active_subscriptions = True

    @api.depends('partner_id')
    def _compute_has_active_tags(self):
        for rec in self:
            if self.partner_id.tag_ids:
                rec.has_active_tags = True

    @api.depends('has_active_tags')
    def _compute_hide_subscription_block(self):
        for rec in self:
            if rec.has_active_tags:
                rec.hide_subscription_block = True
    # endregion

    # region Constrains and Onchange
    @api.onchange('partner_id')
    def _onchange_partner(self):
        return {
            'domain': {
                'tag_id': [('id', 'in', self.partner_id.tag_ids.ids)]
            }
        }
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_close_contract(self):
        """Close the contract of the partner."""
        self.ensure_one()

        if self.close_type == 'date':
            if self.date_close == fields.Date.today():
                end_date = fields.Datetime.now()
            else:
                end_date = self.date_close
        else:
            self.subscription_id.active_line_id.end_date

        apply_prorata = self.prorata_temporis if self.close_type == 'date' else False

        self.subscription_id.update_active_period(closing_date=end_date, prorata=apply_prorata)

        return self._refresh_wizard()

    def action_deallocate_tag(self):
        u"""Désaffectation du tag, c'est à dire clôture immédiate de l'assignation en cours."""
        self.tag_id.deallocate()

        return self._refresh_wizard()
    # endregion

    # region Model methods
    @api.multi
    def _refresh_wizard(self):
        self.ensure_one()

        has_active_subscriptions = self.has_active_subscriptions
        self.unlink()

        # We don't want to redraw the wizard if there is no subscription left to end
        # because the subscription is the last entity to be ended in the wizard
        if not has_active_subscriptions:
            return False

        return {
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new',
        }
    # endregion

    pass
