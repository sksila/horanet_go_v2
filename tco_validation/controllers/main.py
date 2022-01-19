# -*- coding: utf-8 -*-

from odoo.addons.website_portal.controllers.main import website_account

from odoo import _
from odoo.http import request


class WebsiteAccountValidation(website_account):
    def _prepare_portal_layout_values(self):
        """Override account method of OCA website_portal module.

        to be able to display messages if current user has to provide some documents
        """
        context = super(WebsiteAccountValidation, self)._prepare_portal_layout_values()

        user = request.env.user
        alerts = context.get('alerts', False) or []

        # Ces fonctions servent à afficher des messages sur le panel de l'utilisateur
        # Pour la présence de l'adresse :
        if user.partner_id.address_status == 'incomplete':
            message = _(u"Your address is necessary to use our services.")
            alerts.append({
                'text': message,
                'type': 'alert-info',
                'target': '/my/account'
            })
        # Pour l'adresse :
        address_proof = user.get_documents(
            document_type='proof_of_address',
            status=['to_check', 'valid']
        )
        if user.partner_id.address_workflow != 'validated':
            if not address_proof or not address_proof.filtered(lambda r: r.partner_id == user.partner_id):
                message = _(u"In order to validate your account, you must provide "
                            u"a document that justify your current address.")
                alerts.append({
                    'text': message,
                    'type': 'alert-warning',
                    'target': '/my/documents/add?document_type=proof_of_address'
                })

        # Pour le quotient familial :
        quotient_fam_proof = user.get_documents(
            document_type='caf_certificate',
            status=['to_check', 'valid']
        )
        if user.partner_id.quotient_fam < 1000 and not quotient_fam_proof:
            message = _(u"Your family quotient must be validated by a CAF certificate.")
            alerts.append({
                'text': message,
                'type': 'alert-warning',
                'target': '/my/documents/add?document_type=caf_certificate'
            })

        # Pour les membres du foyer :
        for garant in user.partner_id.garant_ids:
            # Pour l'adresse des membres du foyer
            if garant.address_workflow != 'validated':
                address_doc = garant.get_attached_documents(
                    document_type='proof_of_address',
                    status=['to_check', 'valid']
                )
                # On vérifie si il y a un document justificatif
                if garant.address_workflow != 'validated' and not address_doc:
                    # On construit alors un message pour chaque personne
                    message = _(u"You have to justify the address of {person_name}.") \
                        .format(person_name=garant.name)
                    alerts.append({
                        'text': message,
                        'type': 'alert-warning',
                        'target': '/my/documents/add?document_type=proof_of_address&partner_id=' + str(garant.id)
                    })

        # Pour les relations des membres du foyer
        relations_proof = user.get_documents(
            document_type='family_record_book',
            status=['to_check', 'valid']
        )
        if not user.partner_id.is_garant_valid and not relations_proof:
            message = _(u"You must justify the relation with the all the members of your foyer by submitting a "
                        u"family record book.")
            alerts.append({
                'text': message,
                'type': 'alert-warning',
                'target': '/my/documents/add?document_type=family_record_book'
            })

        # On met à jour le contexte pour y inclure nos message :
        if alerts:
            context['alerts'] = alerts

        context.update(context)

        return context
