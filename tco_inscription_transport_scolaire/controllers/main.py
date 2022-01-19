# -*- coding: utf-8 -*-

import base64

from odoo.addons.website_portal.controllers.main import website_account

from odoo.addons.partner_documents.controllers.main import VALID_MIME_TYPES

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools.translate import _

INSCRIPTION_MODEL_FIELD = ['period_id',
                           'responsible_id',
                           'recipient_id',
                           'assist',
                           'assist_phone',
                           'assist2',
                           'assist_phone2',
                           'regime',
                           'school_establishment_id',
                           'is_student',
                           'is_automatic_payment',
                           'transport_titre',
                           'invoice_period',
                           'compte_id',
                           'derogation_type',
                           'has_badge',
                           'family_quotient',
                           'is_als',
                           'school_cycle',
                           'school_grade_id',
                           'is_allowing_picture',
                           'is_allowing_hospitalization',
                           'qf_certificate',
                           'school_enrollment_certificate',
                           'address_certificate']


class WebsiteInscription(website_account):
    """Class used to manage inscriptions in front."""

    @http.route(['/my/inscription/create',
                 '/my/inscription/edit/<int:inscription_id>'],
                type='http', auth='user', website=True, methods=['POST', 'GET'])
    def page_manage_inscription(self, redirect=None, validate=False, *args, **post):
        """Create and edit an inscription."""
        context = dict(request.context)
        user = request.env.user
        partner = user.partner_id
        inscription_model = request.env['tco.inscription.transport.scolaire']
        school_cycles = request.env['horanet.school.cycle'].sudo().search([])
        school_grades = request.env['horanet.school.grade'].sudo().search([])
        user_documents = request.env.user.get_documents(status=['to_check', 'valid']).filtered('document_type_id')\
            .sorted('id')
        document_types = request.env['ir.attachment.type'].search([])
        recipients = partner.search(['|',
                                     '|',
                                     ('search_field_all_foyers_members', 'in', partner.id),
                                     ('id', '=', partner.id),
                                     ('id', 'in', partner.garant_ids.ids)], order="id")
        if not redirect:
            redirect = '/my/requests'
        context.update({
            'user': user,  # Utilisateur courant
            'school_cycles': school_cycles,  # Liste des cycles pour combobox
            'school_grades': school_grades,  # Listes des niveaux scolaires
            'error': {},  # Liste des champs en erreur (avec message)
            'error_message': [],  # Liste des messages d'erreur générique
            'post': {},  # Data du PostBack pour conservation de saisi
            'redirect': redirect,  # Chemin de redirection
            'partner': partner,  # partner de l'utilisateur
            'valid_mime_types': VALID_MIME_TYPES,
            'user_documents': user_documents,
            'recipients': recipients,
            'document_types': document_types,
        })

        # Création de l'objet d'inscription
        if post.get('inscription_id'):
            # Mode edition
            inscription_id = post.get('inscription_id')
            inscription_rec = inscription_model.browse([inscription_id])
            if inscription_rec.status != 'draft' or inscription_rec.responsible_id != partner:
                return request.redirect(redirect)
            inscription_rec.check_access_rights('write')
        else:
            # Mode création
            default_val = inscription_model.default_get(inscription_model.fields_get())
            inscription_rec = inscription_model.new(default_val)
            inscription_rec.responsible_id = partner
            inscription_rec.check_access_rights('create')
        context.update({'inscription': inscription_rec})

        # Primo chargement de la page
        if request.httprequest.method == 'GET':
            return request.render('tco_inscription_transport_scolaire.create_inscription', context)

        # Traitement du formulaire en PostBack
        if request.httprequest.method == 'POST':
            error, error_message = self._form_validate_inscription(post, validate)
            context.update({'error': error, 'error_message': error_message})
            context['post'].update(post)
            if error or error_message:
                return request.render('tco_inscription_transport_scolaire.create_inscription', context)
            else:
                # If no errors, create or update inscription record
                post_values = self.map_dictionary(post, INSCRIPTION_MODEL_FIELD)
                if inscription_rec.status == 'draft' and validate:
                    post_values['status'] = 'to_validate'
                try:
                    # Mode édition
                    if post.get('inscription_id', False):
                        inscription_rec.write(post_values)
                    # Mode création
                    else:
                        inscription_model.create(post_values)
                except ValidationError as ex:
                    request.env.cr.rollback()
                    context.update({'error_message': ex.name.split('\n')})
                    return request.render('tco_inscription_transport_scolaire.create_inscription', context)

        return request.redirect(redirect)

    @http.route(['/my/inscription/delete/<model("tco.inscription.transport.scolaire"):inscription>'],
                type='http', auth='user', website=True, methods=['POST', 'GET'])
    def page_delete_inscription(self, redirect=None, inscription=None, *args, **post):
        """Delete an inscription.

        :return: redirect
        """
        if not redirect:
            redirect = '/my/requests'
        if inscription.status == 'draft' and inscription.responsible_id == request.env.user.partner_id:
            inscription.sudo().unlink()
        return request.redirect(redirect)

    @http.route(['/terms/preview'], type='http', auth='user', method=['GET'], website=True)
    def terms_preview(self):
        """Display the terms and conditions document in a new Tab."""
        terms_document = request.env.ref('tco_inscription_transport_scolaire.tco_terms_and_conditions_document')
        document = request.env['ir.attachment'].browse(terms_document.id)

        if not document or not document.mimetype:
            return request.redirect('/my/home')

        return request.make_response(
            base64.b64decode(document.datas), [
                ('Content-Type', document.mimetype),
            ]
        )

    @staticmethod
    def map_dictionary(origin, keys_list, keys_mapping={}):
        u"""
        Permet de filtrer et mapper les clés d'un dictionnaire.

        :param origin: dictionnaire d'origin à mapper
        :param keys_list: liste des clés à filtrer
        :param keys_mapping: OPTIONNEL,liste des clés à mapper sous forme {'original_name','new_name'}
        :return: dictionnaire filtré/mappé
        """
        return dict(((k in keys_mapping and keys_mapping[k] or k, v) for k, v in origin.iteritems()
                     if k in keys_list or k in keys_mapping))

    @staticmethod
    def _form_validate_inscription(data, validate=False):
        """Validate form data.

        :param dict() data: values of the form
        :return: error : dictionary of invalid fields and list of error description
        :rtype: (error, error_message)
        """
        error = dict()
        error_message = []
        inscription_model = request.env['tco.inscription.transport.scolaire'].sudo()
        mandatory_fields = [
            'responsible_id', 'period_id', 'recipient_id'
        ]

        # Validation
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # Test documents et photo du bénéficiaire, seulement si on valide
        if validate:
            # Erreur si pas de certificat de quotient familial et si celui-ci est < 1000
            if int(data.get('family_quotient', False)) < 1000 and not data.get('qf_certificate', False):
                error['qf_certificate'] = 'error'
                error_message.append(_("A document that validates the QF is required if your QF is inferior to 1000."))
            # en front le certificat d'inscription scolaire est obligatoire
            if not data.get('school_enrollment_certificate', False):
                error['school_enrollment_certificate'] = 'missing'
            # en front le justificatif de domicile est obligatoire
            if not data.get('address_certificate', False):
                error['address_certificate'] = 'missing'
            # Pour la photo
            recipient = request.env.user.partner_id.browse(int(data.get('recipient_id', False)))
            if recipient and not recipient.image:
                error_message.append(_("A picture of the recipient is necessary for an inscription."))

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_("Some required fields are empty."))

        # Validation quotient familial
        if data.get('family_quotient') and not data.get('family_quotient').isdigit():
            error['family_quotient'] = 'error'
            error_message.append(_("Enter a valid family quotient"))

        if data.get('recipient_id') and data.get('period_id'):
            domain = [('recipient_id', '=', int(data.get('recipient_id'))),
                      ('status', 'not in', ['cancelled', 'refused']),
                      ('period_id', '=', int(data.get('period_id')))]
            if data.get('inscription_id', False):
                domain.append(('id', '!=', int(data.get('inscription_id'))))
            existing_rec = inscription_model.search(domain, limit=1)
            if existing_rec:
                error_message.append(
                    _(u"""Il existe déjà une inscription pour {recipient_name} sur la période {period_name}.
                     Responsable : {responsable_name}""").format(
                        recipient_name=unicode(existing_rec.recipient_id.name),
                        period_name=unicode(existing_rec.period_id.name),
                        responsable_name=unicode(existing_rec.responsible_id.name)))

        # test assist phone number
        if data.get('assist_phone'):
            assist_phone = data['assist_phone'].replace(' ', '')
            if not assist_phone.isnumeric() or len(assist_phone) > 10:
                error['assist_phone'] = 'error'
                error_message.append(_("Enter a valid assist phone number."))

        return error, error_message
