from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import safe_eval
from .. import tools as website_tools

try:
    from odoo.addons.website_portal.controllers.main import website_account
except ImportError:
    from website_portal.controllers.main import website_account

PARTNER_MODEL_FIELD = [
    'firstname', 'lastname', 'firstname2', 'lastname2',
    'city_id', 'street_id', 'zip_id', 'state_id', 'country_id',
    'street_number_id', 'street2', 'street3',
    'title', 'phone', 'mobile', 'birthdate_date',
    'image', 'email', 'quotient_fam', 'has_custom_image',
    'vat_number', 'ape_code', 'siret_code', 'country_phone', 'country_mobile', 'cat_tiers_id', 'nat_jur_id',
]


class WebsiteAccount(CustomerPortal):
    """Class of the website account controllers."""

    # On modifie la fonction pour modifier ses infos
    @http.route(['/my/account'], type='http', auth='user', website=True)
    def details(self, redirect='/my/home', *args, **post):
        """Display informations of the accounts and modify them.

        info: class overridden by 'horanet_demat_ormc_psv2' to add NatJur and CatTiers.
        """
        # Ajouter le contexte courant à qweb
        context = dict(request.context)
        user = request.env.user

        context.update({
            'user': user,  # Utilisateur courant
            'partner': user.partner_id,
            'error': {},  # Liste des champs en erreur (avec message)
            'error_message': [],  # Liste des messages d'erreur générique
            'mode_creation': not bool(user.partner_id),  # Pour différencier le mode création/édition
            'partner_titles': request.env['res.partner.title'].search([('is_company_title', '=', False)]),
            'company_titles': request.env['res.partner.title'].search([('is_company_title', '=', True)]),
            'post': post,  # Data du PostBack pour conservation de saisi
            'redirect': redirect  # Chemin de redirection
        })

        # For options
        additional_context = self.user_add_options(user, post)
        context.update(additional_context)

        # Primo chargement de la page
        if request.httprequest.method == 'GET':
            try:
                context['image_base64'] = website_tools.image.get_default_partner_image(user.partner_id)
            except IOError:
                raise ValueError("Non-image binary fields can not be converted to HTML")
            except Exception as e:  # image.verify() throws "suitable exceptions", I have no idea what they are
                raise e

            return request.render('horanet_website_account.horanet_my_details', context)

        # Traitement du formulaire en PostBack
        if request.httprequest.method == 'POST':
            error = dict()
            error_message = []
            # Récupération de l'image sélectionné pour l'ajouter au post (pour affichage/enregistrement)
            if post.get('input_avatar'):
                image_base64, error_img = website_tools.image.get_base64_img_avatar_from_file(post['input_avatar'])
                if error_img:
                    error_message.append(error_img)
                else:
                    # Garder l'image précédente en cas d'erreur
                    post['has_custom_image'] = True

            post['country_mobile_code'] = post['country_mobile']
            post['country_phone_code'] = post['country_phone']

            # Validation des données du formulaire
            error_validation, error_message_validation = website_tools.partner. \
                form_validate(post, is_company=user.partner_id.is_company, validate_address=True, user=user)

            post['phone'] = post['phone'].replace(' ', '').replace('-', '').replace('.', '').replace('/', '')
            post['mobile'] = post['mobile'].replace(' ', '').replace('-', '').replace('.', '').replace('/', '')

            error.update(error_validation)
            error_message.extend(error_message_validation)
            context.update({'error': error, 'error_message': error_message})
            context['post'].update(post)

            if error or error_message:
                # Affichage du formulaire avec ses erreurs
                return request.render('horanet_website_account.horanet_my_details', context)
            else:
                try:
                    # If no errors, create or update partner record
                    self.user_write_data(user, post)
                except ValidationError as vex:
                    request.env.cr.rollback()
                    context.update({'error_message': vex.name.split('\n')})
                    return request.render('horanet_website_account.horanet_my_details', context)
                except Exception as e:
                    # S'assurer du rollback en cas d'erreur (non géré en frontend)
                    e.args = ('Catching exception to force cursor rollback',)
                    request.env.cr.rollback()
                    raise

        return request.redirect(redirect)

    def user_add_options(self, user, data):
        """
        Get the options like additional addresses.

        :param user: the current user
        :param data: the data of the form
        :return: the context with additional informations
        """
        context = {}

        # We get all the parameters
        icp_model = request.env['ir.config_parameter'].sudo()
        if 'country_id' not in data:
            default_country_id = safe_eval(icp_model.get_param(
                'horanet_website_account.default_country_id', 'False'
            ))
            context['default_country_id'] = default_country_id

        context['default_country_phone_code'] = user.country_phone
        context['default_country_mobile_code'] = user.country_mobile

        # For all the additional informations section
        # The section will be displayed if this is True
        context['additional_informations'] = False
        # To know if we have to display a family quotient input
        use_family_quotient = safe_eval(icp_model.get_param(
            'partner_contact_personal_information.group_add_personal_family_quotient', 'False'
        ))
        if use_family_quotient:
            context['use_family_quotient'] = True
            context['additional_informations'] = True

        # Si le partner a une adresse de facturation
        invoice_address = user.partner_id.child_ids.filtered(lambda r: r.type == 'invoice')
        if invoice_address:
            context['invoice_address'] = invoice_address[0]
        # Si le partner a une adresse de livraison
        shipping_address = user.partner_id.child_ids.filtered(lambda r: r.type == 'delivery')
        if shipping_address:
            context['shipping_address'] = shipping_address[0]

        return context

    def user_write_data(self, user, data):
        """
        Write the data on the user.

        :param user: user to write data in
        :param data: all the data from the account page
        :return:
        """
        if data.get('image_base64') and data['image_base64'].startswith('data:'):
            data['image_base64'] = data['image_base64'].split(',')[1]
        post_values = website_tools.partner.prepare_fields(data)
        post_values = website_tools.partner.map_dictionary(post_values, PARTNER_MODEL_FIELD,
                                                           {'image_base64': 'image'})

        user.partner_id.write(post_values)

        invoice_address = user.partner_id.child_ids.filtered(lambda r: r.type == 'invoice')
        shipping_address = user.partner_id.child_ids.filtered(lambda r: r.type == 'delivery')

        # Si il y a une adresse de facturation, on la créer
        if data.get('has_invoice_address', False):
            website_tools.address.create_invoice_address(user.partner_id, data)
        # Si il y a une adresse de facturation et on décoche la case, alors on supprime l'adresse
        elif not data.get('has_invoice_address', False) and invoice_address:
            invoice_address[0].sudo().unlink()
        # Si il y a une adresse de livraison, on la créer
        if data.get('has_shipping_address', False):
            website_tools.address.create_shipping_address(user.partner_id, data)
        # Si il y a une adresse de livraison et on décoche la case, alors on supprime l'adresse
        elif not data.get('has_shipping_address', False) and shipping_address:
            shipping_address[0].sudo().unlink()
