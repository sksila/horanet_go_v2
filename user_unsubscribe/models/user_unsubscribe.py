# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, exceptions


class UserUnsubscribe(models.Model):
    # region Private attributes
    _name = 'user.unsubscribe'
    _order = 'id desc'
    _inherit = ['ir.needaction_mixin', 'mail.thread']
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", compute='_compute_unsubscription_name')
    user_id = fields.Many2one(string="User", comodel_name='res.users', required=True)
    partner_id = fields.Many2one(string="Related partner", related='user_id.partner_id', readonly=True)
    date = fields.Datetime(string="Date of request", default=fields.Datetime.now)
    status = fields.Selection(string="Status", selection=[('pending', 'Pending'), ('accepted', 'Accepted'),
                                                          ('cancelled', 'Cancelled')], default='pending')
    write_date = fields.Datetime(string="Last action on", readonly=True)
    refuse_reason = fields.Char(string="Refuse reason")

    # endregion

    # region Fields method
    @api.depends('user_id')
    def _compute_unsubscription_name(self):
        """Compute the name the same as the user_id."""
        for rec in self:
            if rec.user_id:
                rec.name = rec.user_id.name

    # endregion

    # region Constrains and Onchange
    @api.constrains('status')
    def _check_status_constrains(self):
        """Check if there is no 2 pending requests for the same person."""
        for rec in self:
            list_error_message = []
            if rec.status == 'pending':
                duplicate = self.env['user.unsubscribe'].search_count([
                    ('status', '=', 'pending'),
                    ('user_id', '=', self.user_id.id),
                    ('id', '!=', self.id)
                ])
                if duplicate:
                    list_error_message.append(_("A request for this user has already been fulfilled"))

            # We prevent a request for the admin
            if rec.user_id.id == 1:
                list_error_message.append(_("The admin cannot unsubscribe."))

            if list_error_message:
                raise exceptions.ValidationError('\n'.join(list_error_message))
                # endregion

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """We send a mail when the request is created."""
        new_request = super(UserUnsubscribe, self).create(vals)
        template = self.env.ref('user_unsubscribe.unsubscribe_pending')
        template.sudo().send_mail(new_request.id, force_send=True)

        return new_request

    # Pour le needaction
    @api.model
    def _needaction_domain_get(self):
        """To have a needaction on the menu. We show pending requests."""
        return [('status', '=', 'pending')]

    # endregion

    # region Actions
    def action_pending(self):
        """Set the request on pending."""
        if self.status != 'pending':
            self.status = 'pending'

    def action_accept(self):
        """Set the request on accepted. Set the user on active = False and send a mail."""
        if self.status not in ['accepted', 'cancelled']:
            self.status = 'accepted'

            # We set the user on active = False with sudo()
            self.sudo().user_id.active = False

            template = self.env.ref('user_unsubscribe.unsubscribe_accepted')
            template.sudo().send_mail(self.id, force_send=True)

    # endregion

    # region Model methods
    # endregion

    pass
