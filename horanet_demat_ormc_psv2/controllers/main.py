# -*- coding: utf-8 -*-
from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from .. import tools as horanet_demat_tools

try:
    from odoo.addons.horanet_website_account.controllers.main import website_account
    from odoo.addons.horanet_website_account import tools as website_tools
except ImportError:
    from horanet_website_account.controllers.main import website_account
    from horanet_website_account import tools as website_tools


class WebsiteAccount(website_account):

    @http.route()
    def details(self, redirect='/my/home', *args, **post):

        # Override of horanet_website_account to add CatTiers and NatJur informations.
        signup = super(WebsiteAccount, self).details(*args, **post)
        user = request.env.user

        signup.qcontext.update({
            'user': user,  # Utilisateur courant
            'partner': user.partner_id,
            'error': {},  # Liste des champs en erreur (avec message)
            'mode_creation': not bool(user.partner_id),  # Pour différencier le mode création/édition
            'partner_titles': request.env['res.partner.title'].search([('is_company_title', '=', False)]),
            'company_titles': request.env['res.partner.title'].search([('is_company_title', '=', True)]),
            'post': post,  # Data du PostBack pour conservation de saisi
            'redirect': redirect,  # Chemin de redirection
            'nat_jur': request.env['pes.referential.value'].search([
                ('ref_id', '=', request.env.ref('horanet_demat_ormc_psv2.pes_ref_nat_jur').id),
                ('name', '!=', "Particuliers")]),
            'nat_jur_message': str(request.env['collectivity.config.settings'].get_nat_jur_help()),
            'cat_tiers': request.env['pes.referential.value'].search([
                ('ref_id', '=', request.env.ref('horanet_demat_ormc_psv2.pes_ref_cat_tiers').id)]),
            'cat_tiers_message': str(request.env['collectivity.config.settings'].get_cat_tiers_help()),
            'required_nat_jur': request.env['collectivity.config.settings'].get_required_nat_jur(),
            'required_cat_tiers': request.env['collectivity.config.settings'].get_required_cat_tiers(),
        })

        # # Primo chargement de la page
        if request.httprequest.method == 'GET':
            return request.render('horanet_website_account.horanet_my_details', signup.qcontext)

        if request.httprequest.method == 'POST':
            error = signup.qcontext['error'] if signup.qcontext.get('error', False) else dict()
            error_message = signup.qcontext['error_message'] if signup.qcontext.get('error_message', False) else []

            # Validation du CatTiers et NatJur du formulaire
            error_validation, error_message_validation = horanet_demat_tools.utils. \
                form_validate_nat_jur_cat_tiers(post, is_company=user.partner_id.is_company)

            # Récupération de l'image sélectionné pour l'ajouter au post (pour affichage/enregistrement)
            if post.get('input_avatar'):
                image_base64, error_img = website_tools.image.get_base64_img_avatar_from_file(post['input_avatar'])
                if error_img:
                    error_message.append(error_img)
                else:
                    # Garder l'image précédente en cas d'erreur
                    post['image_base64'] = image_base64
                    post['has_custom_image'] = True

            error.update(error_validation)
            error_message.extend(error_message_validation)
            signup.qcontext.update({'error': error, 'error_message': error_message})
            signup.qcontext['post'].update(post)

            if error or error_message:
                # Affichage du formulaire avec ses erreurs
                return request.render('horanet_website_account.horanet_my_details', signup.qcontext)
            else:
                try:
                    # If no errors, create or update partner record
                    self.user_write_data(user, post)
                except ValidationError as vex:
                    request.env.cr.rollback()
                    signup.qcontext.update({'error_message': vex.name.split('\n')})
                    return request.render('horanet_website_account.horanet_my_details', signup.qcontext)
                except Exception as e:
                    # S'assurer du rollback en cas d'erreur (non géré en frontend)
                    e.args = ('Catching exception to force cursor rollback',)
                    request.env.cr.rollback()
                    raise

        return signup
