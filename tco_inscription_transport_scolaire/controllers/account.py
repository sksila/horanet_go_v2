# -*- coding: utf-8 -*-

from odoo.addons.tco_validation.controllers.main import WebsiteAccountValidation

from odoo import _
from odoo.http import request


class WebsiteAccountInscription(WebsiteAccountValidation):
    def _prepare_portal_layout_values(self):
        """Override account method of OCA website_portal module.

        to be able to display messages if current user has to provide some documents
        """
        context = super(WebsiteAccountInscription, self)._prepare_portal_layout_values()

        user = request.env.user
        alerts = context.get('alerts') or []

        # Pour les inscriptions TCO
        inscriptions = request.env['tco.inscription.transport.scolaire'].sudo().search(
            [('responsible_id', '=', user.partner_id.id),
             ('status', 'in', ['draft', 'to_validate'])]
        )
        for inscription in inscriptions:
            if inscription.recipient_id:
                school_proof = inscription.recipient_id.get_attached_documents(
                    document_type='school_enrollment_certificate',
                    status=['to_check', 'valid']
                )
                if not school_proof:
                    message = _(
                        u"You have to justify the inscription to school transport for {person_name} with a school "
                        u"enrollment certificate.").format(person_name=inscription.recipient_id.name)
                    alerts.append({
                        'text': message,
                        'type': 'alert-warning',
                        'target': '/my/documents/add?document_type=school_enrollment_certificate&partner_id=' + str(
                            inscription.recipient_id.id)
                    })
                if not inscription.recipient_id.has_custom_image:
                    message = _(
                        u"You have to provide an identity picture of {person_name} for the school transport "
                        u"inscription.").format(person_name=inscription.recipient_id.name)
                    alerts.append({
                        'text': message,
                        'type': 'alert-warning',
                        'target': '/my/foyers/edit/member/' + str(
                            inscription.recipient_id.id)
                    })

        if inscriptions.filtered('is_automatic_payment'):
            rib_document = user.partner_id.get_attached_documents(
                document_type='bank_details',
                status=['to_check', 'valid']
            )

            if not rib_document:
                message = _("You have to provide your bank details as one of "
                            "your inscriptions is using direct debit mode.")
                alerts.append({
                    'text': message,
                    'type': 'alert-warning',
                    'target': '/my/documents/add?document_type=bank_details',
                })

        # On met à jour le contexte pour y inclure nos message :
        if alerts:
            context['alerts'] = alerts

            context.update(context)

        return context
