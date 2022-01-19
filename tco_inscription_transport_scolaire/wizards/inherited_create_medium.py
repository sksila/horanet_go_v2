# coding: utf-8

from odoo import api, fields, models


class CreateMedium(models.TransientModel):
    """Override wizard to allow settings `badge_id` on partner's inscriptions."""

    _inherit = 'partner.contact.identification.wizard.create.medium'

    @api.model
    def create_medium(self, tag_ids, type_id=False):
        """Assign the created medium to partner's inscriptions."""
        super(CreateMedium, self).create_medium(tag_ids, type_id)

        medium_model = self.env['partner.contact.identification.medium']
        medium = medium_model.search([
            ('tag_ids', 'in', [tag_id for tag_id in tag_ids])
        ])

        partner = medium.partner_id

        inscription_model = self.env['tco.inscription.transport.scolaire']
        inscriptions = inscription_model.search([
            ('recipient_id', '=', partner.id),
            ('status', '!=', 'cancelled'),
            ('date_end', '>', fields.Date.today())
        ])

        if inscriptions:
            inscriptions.write({
                'has_badge': True,
                'badge_id': medium.id
            })
