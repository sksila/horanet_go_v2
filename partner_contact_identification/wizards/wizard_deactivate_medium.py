from odoo import api, models


class DeactivateMedium(models.TransientModel):
    """Allow deactivation of a medium."""

    _name = 'partner.contact.identification.wizard.deactivate.medium'

    @api.model
    def deactivate_mediums(self):
        """Deactivate one or multiple mediums."""
        mediums = self.env['partner.contact.identification.medium'].browse(
            self.env.context.get('active_ids')
        )
        mediums.deactivate()
