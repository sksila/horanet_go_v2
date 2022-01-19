# -*- coding: utf-8 -*-

import logging

from odoo.addons.partner_type_foyer.controllers.main import WebsiteAccountFoyer

from odoo import _


_logger = logging.getLogger(__name__)


class InheritedWebsiteAccountFoyer(WebsiteAccountFoyer):

    def _validate_form(self, values, partner):
        """Override the function to force people to put birthdate and picture."""
        values, errors, errors_messages = super(InheritedWebsiteAccountFoyer, self)._validate_form(values, partner)

        if not values.get('input_avatar', False) and not partner.image and not values.get('image_base64', False):
            errors['input_avatar'] = 'error'
            errors_messages.append(_("A picture of the recipient is necessary for an inscription."))

        if not values.get('birthdate_date', False):
            errors['birthdate_date'] = 'error'
            errors_messages.append(_("The birthdate of the recipient is necessary for an inscription"))

        return values, errors, errors_messages
