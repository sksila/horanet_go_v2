# coding: utf-8

from odoo import api, fields, models


class RefuseUnsubscription(models.TransientModel):
    """The wizard to register a reason when you refuse an unsubscription."""

    _name = 'user.unsubscribe.refuse'

    request_id = fields.Many2one(string='Inscription', comodel_name='user.unsubscribe')
    reason = fields.Text(string='Reason', required=True)

    @api.multi
    def action_refuse(self):
        """
        Refuse the inscription with a reason.

        Set the user on active = True if he want to have access back to his account.
        """
        self.request_id.refuse_reason = self.reason
        self.request_id.status = 'cancelled'

        template = self.env.ref('user_unsubscribe.unsubscribe_refused')
        template.sudo().send_mail(self.request_id.id, force_send=True)

        # If the user was inactive, we set him on active if he want access back to his panel.
        if not self.request_id.user_id.active:
            self.sudo().request_id.user_id.active = True
