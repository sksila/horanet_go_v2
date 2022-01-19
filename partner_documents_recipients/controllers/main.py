from odoo.addons.partner_documents.controllers.main import WebsitePortalDocuments

from odoo import _, http
from odoo.http import request


class InheritedWebsitePortalDocuments(WebsitePortalDocuments):

    def _get_partners_related(self, partner):
        """Return partners that are under responsability / in the foyer of partner.

        :param partner: partner to search related partners
        :return: partner recordset
        """
        recipients = partner.search([
            '|', '|',
            ('search_field_all_foyers_members', 'in', partner.id),
            ('id', '=', partner.id),
            ('id', 'in', partner.garant_ids.ids)
        ], order="id")

        return recipients

    def extra_validation(self, values):
        """Use this method if you want to implement your own validation logic on existing fields or new fields.

        :param values: custom input values
        :return: input errors that will be displayed to the user
        :rtype: {}
        """
        errors = super(InheritedWebsitePortalDocuments, self) \
            .extra_validation(values)

        recipient = values.get('recipient')
        recipients = values.get('recipients')

        try:
            if int(recipient) not in recipients.ids:
                errors['err_recipient'] = _('Wrong recipient selected.')
        except ValueError:
            errors['err_recipient'] = _('Wrong recipient selected.')
            # This will overwrite the recipient key of the context dict
            errors['recipient'] = None

        return errors

    def custom_attachment_values(self, custom_values):
        """Use this method if you want to add custom values to an ir.attachment.

        :param values: custom input values
        :return: values that will be written on ir.attachment object
        :rtype: {}
        """
        values = super(InheritedWebsitePortalDocuments, self) \
            .custom_attachment_values(custom_values)

        values.update({'partner_id': int(custom_values.get('recipient'))})

        return values

    @http.route()
    def add_document(self, redirect=None, document_type=None, partner_id=False, **kw):
        """Display a form that allow current user to send documents.

        The user is able to select himself or its related partners as the
        partner attached to the ir.attachment and the type of the document he
        wants to create

        :param redirect: where to redirect the user
        :param document_type: value used to select the document_type select input
        :param partner_id: the preselected partner
        :param kw: custom input values
        """
        default_recipient_id = partner_id or kw.get('recipient', False)
        kw.update({
            'recipient': default_recipient_id,
            'recipients': self._get_partners_related(request.env.user.partner_id),
        })

        return super(InheritedWebsitePortalDocuments, self) \
            .add_document(redirect, document_type, **kw)
