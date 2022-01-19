import ast

from odoo.addons.partner_documents.controllers.main import VALID_MIME_TYPES
from odoo.addons.portal.controllers.portal import CustomerPortal as website_account

from odoo import http, _
from odoo.exceptions import ValidationError, AccessDenied
from odoo.http import request
from odoo.osv import expression
from odoo.tools import safe_eval


class WebsitePortalApplications(website_account):
    @http.route()
    def home(self, **kw):
        """Add requests to main home page and a counter."""
        response = super(WebsitePortalApplications, self).home(**kw)
        user = request.env.user

        requests = request.env['website.application']

        application_count = requests.search_count([('applicant_id', '=', user.id)])

        request_count = application_count

        response.qcontext.update({
            'request_count': request_count,
        })
        return response

    @http.route(['/my/requests'], type='http', auth='user', method=['GET'], website=True)
    def get_requests(self, date_begin=None, date_end=None):
        """Display all requests owned by the current user."""
        template_name = 'website_application.requests'
        context = self._prepare_portal_layout_values()

        # On va chercher les demandes de l'utilisateur, le filtre se fait par un ir.rule
        domain = []
        archive_groups = self._get_archive_groups('website.application', domain)
        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<', date_end)]

        domain += [('applicant_id', '=', request.env.uid)]
        user_requests = request.env['website.application'].sudo().search(domain)

        # On va chercher les modèles de demandes actifs (mais pas ceux sans demande multiple si déjà demandés)
        request_templates = get_available_requests(request.env.user, user_requests)

        context.update({
            'website_requests': user_requests,
            'request_templates': request_templates,
            'archive_groups': archive_groups,
            'date': date_begin
        })

        return request.render(template_name, context)

    @http.route(['/my/requests/<string:application_type>'], type='http', auth='user', method=['GET'], website=True)
    def get_application_requests(self, application_type, date_begin=None, date_end=None):
        response = self.get_requests(date_begin, date_end)

        request_templates = response.qcontext.get('request_templates', False)
        website_requests = response.qcontext.get('website_requests', False)

        if application_type not in \
                dict(request.env['website.application.template'].sudo()._fields['application_type'].selection):
            # Si le type d'application demandé n'existe pas, on affiche les téléservices dont le type d'application
            # n'est pas renseigné (téléservices généraux)
            application_type = False

        if request_templates:
            response.qcontext.update({
                'request_templates': request_templates.filtered(lambda rt: rt.application_type == application_type),
            })

        if website_requests:
            response.qcontext.update({
                'website_requests': website_requests.filtered(
                    lambda wr:
                    wr.website_application_template_id
                    and wr.website_application_template_id.application_type == application_type),
            })

        return response


class WebsiteApplications(http.Controller):
    @http.route(['/my/requests/<int:request_id>'], type='http', auth='user', website=True)
    def get_request(self, request_id, **post):
        """Get the request and create a new message if necessary."""
        template_name = 'website_application.see_request'
        web_request = request.env['website.application'].browse(request_id)

        attachment_ids = []
        if web_request.attachment_ids:
            attachment_ids = request.env.user.get_documents().search([('id', 'in', web_request.attachment_ids.ids)])

        information_ids = []
        if web_request.application_information_ids:
            information_ids = request.env['application.information'].sudo() \
                .search([('id', 'in', web_request.application_information_ids.ids)])

        qcontext = {
            'web_request': web_request,
            'request_id': request_id,
            'post': post,
            'attachment_ids': attachment_ids,
            'information_ids': information_ids
        }

        if request.httprequest.method == 'POST':
            if post.get('message', False):
                request.env['website.application.message'].create({'application_id': request_id,
                                                                   'text': post.get('message'),
                                                                   'user_id': request.env.user.id})

        return request.render(template_name, qcontext)

    @http.route(['/my/requests/create'], type='http', auth='user', website=True)
    def create_request(self, request_type=False, **post):
        """Process the request."""
        # Si c'est un modèle d'application
        if request_type and request_type.isdigit():

            user_requests = request.env['website.application'].sudo().search([('applicant_id', '=', request.env.uid)])

            # On va chercher le modèle si il est demandes actif (mais pas si sans demande multiple déjà demandé)
            request_template = get_available_requests(request.env.user, user_requests, request_type)

            # Rediriger l'utilisateur vers la page 404 si pas de template
            if not request_template:
                raise AccessDenied()

            # Rediriger l'utilisateur vers la page d'informations personnelles si indiqué comme tel sur le template
            partner = request.env.user.partner_id
            if request_template.ask_partner_informations:
                if not partner.city_id or not partner.street_id:
                    return request.redirect(
                        '/my/account?redirect=/my/requests/create?request_type=' + request_type)

        template_name = 'website_application.create_request'
        context = self.set_context(request_type, post)

        if request.httprequest.method == 'POST':
            if request_type:
                post['request_type'] = request_type

                errors = self.post_values(post, request.env.user)

                if not errors:
                    if context.get('current_stage') == context.get('stages')[len(context.get('stages')) - 1]:
                        return request.redirect('/my/requests')
                    else:
                        index_next_stage = context.get('stages').index(context.get('current_stage')) + 1
                        context.update({'current_stage': context.get('stages')[index_next_stage]})
                        request.render(template_name, context)
                else:
                    context.update({'errors': errors})
                    request.render(template_name, context)

        return request.render(template_name, context)

    def set_context(self, rtype, parameters):
        """Set the context based on parameters."""
        context = {
            'web_application': request.env['website.application'],
            'post': parameters,
            'request_type': rtype,
            'user': request.env.user,
            'partner': request.env.user.partner_id,
        }

        # Si c'est un modèle d'application
        if rtype and rtype.isdigit():
            request_template = request.env['website.application.template'].browse(int(rtype))

            # Ajout des bénéficiaires
            if request_template.is_recipient_to_select and request_template.recipient_domain:
                recipients = request.env['res.partner'].search(ast.literal_eval(request_template.recipient_domain))
            else:
                recipients = request.env['res.partner'].search([], limit=30)

            # Ajout des types de documents requis
            required_document_types = request.env['ir.attachment.type'].search([
                ('id', 'in', request_template.attachment_types.ids)
            ])

            # Ajout de tous les types de documents (pour les infos de type document dans la modale)
            document_types = request.env['ir.attachment.type'].search([])

            # Ajout des documents de l'utilisateur
            user_documents = request.env.user.get_documents(status=['to_check', 'valid']).sorted('id')

            # Ajout des informations à demander
            other_informations = request.env['application.information'].search([
                ('id', 'in', request_template.application_informations.ids)
            ])

            # Ajout des étapes
            stages = other_informations.mapped('website_application_stage_id.name')
            if not other_informations or not other_informations[len(other_informations) - 1] \
                    .website_application_stage_id:
                stages.append('')  # Les informations sans étape sont à la fin

            current_stage = parameters.get('current_stage', stages[0])

            # Mise à jour du contexte
            context.update({
                'request_template': request_template,
                'recipients': recipients,
                'required_document_types': required_document_types,
                'document_types': document_types,
                'other_informations': other_informations,
                'stages': stages,
                'current_stage': current_stage,
                'valid_mime_types': VALID_MIME_TYPES,
                'user_documents': user_documents
            })

        return context

    def post_values(self, values, user):
        """Create the request according to its type. Can be overrided to add more types of request.

        :param values: values of the post
        :param user: user posting the request
        :return: errors with error messages or False
        """
        errors = []
        # Insert code here

        # Si c'est un modèle d'application
        try:
            if values.get('request_type', '').isdigit():
                # On récupère le modèle d'application
                request_template = request.env['website.application.template'].browse(
                    int(values['request_type']))

                # Pour des justificatifs
                attachments_list = []
                document_types = request.env['ir.attachment.type'].sudo().search([
                    ('id', 'in', request_template.attachment_types.ids)
                ])

                for document_type in document_types:
                    document_files = request.httprequest.form.getlist('document_' + str(document_type.id))
                    values['document_' + str(document_type.id)] = document_files
                    if document_files:
                        for document_file in document_files:
                            attachments_list.append(int(document_file))
                    else:
                        errors.append(
                            _("You must submit a ") + document_type.name[0].lower() + document_type.name[1:] + ".")

                if request_template.is_recipient_to_select \
                        and (not values.get('recipient_id', False) or values['recipient_id'] == 'no_one'):
                    errors.append(
                        _("You must select a recipient."))

                stages = safe_eval(values.get('stages')) or []

                # Création des records des informations complémentaires
                other_informations_list = []
                other_informations = request.env['application.information'].sudo().search([
                    ('id', 'in', request_template.application_informations.ids)
                ])
                for other_information in other_informations:
                    other_information_value = values.get('information_' + str(other_information.id), False)

                    if other_information_value:
                        new_information = other_information.copy({'mode': 'result'})
                        new_information.write({
                            'value': other_information_value,
                        })
                        other_informations_list.append(new_information.id)

                    if other_information.type == 'document':
                        document_files = request.httprequest.form.getlist(
                            'document_' + str(other_information.document_type_id.id))
                        values['document_' + str(other_information.document_type_id.id)] = document_files
                        if document_files:
                            for document_file in document_files:
                                attachments_list.append(int(document_file))

                if not errors and stages and values.get('current_stage') == stages[len(stages) - 1]:

                    request.env['website.application'].create({
                        'website_application_template_id': int(values['request_type']),
                        'attachment_ids': [(6, 0, attachments_list)],
                        'recipient_id': values.get('recipient_id', request.env.user.partner_id.id),
                        'application_information_ids': [(6, 0, other_informations_list)],
                        'applicant_id': user.id,
                        'messages_ids':
                            values.get('description', False) and
                            values['description'].strip() and
                            [(0, 0, {'text': values.get('description'), 'user_id': user.id})] or
                            False
                    })
        except ValidationError as exs:
            request.env.cr.rollback()
            for ex in exs.name.split('\n'):
                errors.append(ex)

        return errors


def get_available_requests(user, user_requests, request_type=False):
    domain = []

    if request_type:
        domain = [('id', '=', int(request_type))]

    domain = expression.AND([domain, [
        ('state', '=', 'active'),
        '|',
        '|',
        ('is_recipient_to_select', '=', True),
        ('multiple_requests_allowed', '=', True),
        ('id', 'not in',
         user_requests.filtered(lambda a: a.state != 'rejected').mapped('website_application_template_id').ids)
    ]])

    available_requests = request.env['website.application.template'].search(domain).filtered(
        lambda rt:
        not rt.subscription_category_partner_ids or
        user.partner_id.subscription_category_ids & rt.subscription_category_partner_ids)

    return available_requests
