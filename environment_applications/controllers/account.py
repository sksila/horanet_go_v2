# -*- coding: utf-8 -*-

from odoo import _
from odoo.addons.website_portal.controllers.main import website_account
from odoo.http import request


class WebsiteAccountValidation(website_account):
    def _prepare_portal_layout_values(self):
        """Override to add alerts."""
        context = super(WebsiteAccountValidation, self)._prepare_portal_layout_values()
        user = request.env.user
        alerts = context.get('alerts') or []

        # Ces fonctions servent à afficher des messages sur le panel de l'utilisateur
        # Pour la présence de l'adresse :
        if not user.partner_id.city_id or not user.partner_id.street_id:
            message = _(u"Your address is necessary to apply requests.")
            alerts.append({
                'text': message,
                'type': 'alert-info',
                'target': '/my/account?redirect={}'.format(request.httprequest.path)
            })

        context.update({
            'alerts': alerts,
        })
        return context
