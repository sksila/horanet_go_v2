# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class WebsiteApplication(models.Model):
    """Class of the applications to add more types."""

    # region Private attributes
    _inherit = 'website.application'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_create_medium(self):
        """Open the wizard to create the medium."""
        view = self.env.ref('partner_contact_identification.wizard_create_medium_form')
        # We set the default_reference_id like this to create the medium
        return {
            'name': 'Create medium',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.contact.identification.wizard.create.medium',
            'type': 'ir.actions.act_window',
            'view_id': view.id,
            'context': {'default_reference_id': self.recipient_id.id},
            'target': 'new',
        }
    # endregion

    # region Model methods
    # endregion

    pass
