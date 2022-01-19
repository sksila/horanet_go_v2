# coding: utf-8

from odoo import api, fields, models


class RefuseInscription(models.TransientModel):
    """The wizard to register a reason when you refuse an inscription."""

    _name = 'tco.inscription.refuse'

    inscription_id = fields.Many2one(string='Inscription', comodel_name='tco.inscription.transport.scolaire')
    reason = fields.Text(string='Reason', required=True)

    @api.multi
    def action_refuse(self):
        """Refuse the inscription with a reason."""
        self.inscription_id.refuse_reason = self.reason
        self.inscription_id.status = 'refused'
        template = self.env.ref('tco_inscription_transport_scolaire.email_template_inscription_refused')
        template.sudo().send_mail(self.inscription_id.id, force_send=True)
