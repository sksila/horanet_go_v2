import logging
from datetime import datetime

from odoo.addons.horanet_website_account import tools as website_tools

from odoo import http, tools
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)
MEMBER_MODEL_FIELD = [
    'firstname', 'lastname', 'firstname2', 'lastname2',
    'city_id', 'street_id', 'zip_id', 'state_id', 'country_id',
    'street_number_id', 'street2', 'street3',
    'title', 'phone', 'birthdate_date',
    'image', 'email', 'has_custom_image'
]


class WebsiteAccountFoyer(http.Controller):
    """Class of the controllers of foyers."""

    @http.route(['/my/foyers'], type='http', auth='user', website=True)
    def foyers(self, add_new_foyer=False, redirect='/', **post):
        """Affiche les foyers et les membres."""
        first_foyer = False
        user = request.env.user

        # Récupération du premier foyer si il existe
        if user.foyer_relation_ids:
            active_foyers = [relation.foyer_id for relation in request.env.user.foyer_relation_ids if relation.is_valid]
            first_foyer = (active_foyers and active_foyers[0]) or False
        # Si l'utilisateur est un foyer (ne devrait pas se produire)
        elif request.env.user.company_type == 'foyer':
            first_foyer = request.env.user.partner_id
        else:
            user.partner_id.action_add_foyer()
            active_foyers = [relation.foyer_id for relation in request.env.user.foyer_relation_ids if relation.is_valid]
            first_foyer = (active_foyers and active_foyers[0]) or False

        qweb_context = {
            'user': request.env.user,
            'foyer': first_foyer,
            'partner': user.partner_id,
        }
        return request.render('partner_type_foyer.my_foyers', qweb_context)

    @http.route(['/my/foyers/create/member',
                 '/my/foyers/edit/member/<int:member_id>'],
                type='http', auth='user', website=True, methods=['POST', 'GET'])
    def cru_foyer_member(self, redirect='/my/foyers', member_id=None, *args, **post):
        """Create and edit a foyer member."""
        # Ajouter le contexte courant à qweb
        context = dict(request.context)
        user = request.env.user
        partner_model = request.env['res.partner']
        context.update({
            'user': user,  # Utilisateur courant
            'error': {},  # Liste des champs en erreur (avec message)
            'error_message': [],  # Liste des messages d'erreur générique
            'mode_creation': not bool(member_id),  # Pour différencier le mode création/édition
            'partner_titles': request.env['res.partner.title'].search([]),
            'post': post,  # Data du PostBack pour conservation de saisi
            'redirect': redirect  # Chemin de redirection
        })

        if 'country_id' not in post:
            icp_model = request.env['ir.config_parameter'].sudo()
            default_country_id = safe_eval(icp_model.get_param(
                'horanet_website_account.default_country_id', 'False'
            ))
            context['default_country_id'] = default_country_id

        # Récupérer la liste des foyers actif de l'utilisateur
        foyers = user.foyer_relation_ids.filtered('is_valid').mapped('foyer_id')
        # Si l'utilisateur n'a pas de foyer, abandonner la page
        if not foyers:
            return request.redirect(redirect)

        # Provisoirement prendre le premier foyer comme foyer (les user ne doivent avoir qu'un foyer)
        foyer = foyers[0]
        context.update({'foyer': foyer})

        # Création de l'objet partner
        if member_id:
            # Mode edition
            partner_model.check_access_rights('write')
            member_rec = partner_model.browse([member_id])
        else:
            # Mode création
            partner_model.check_access_rights('create')
            default_val = partner_model.default_get(partner_model.fields_get())
            default_val['lastname'] = user.partner_id.lastname
            default_val['city_id'] = user.partner_id.city_id
            default_val['street_id'] = user.partner_id.street_id
            default_val['zip_id'] = user.partner_id.zip_id
            default_val['country_id'] = user.partner_id.country_id
            default_val['state_id'] = user.partner_id.state_id
            default_val['street_number_id'] = user.partner_id.street_number_id
            default_val['street2'] = user.partner_id.street2
            member_rec = partner_model.new(default_val)

        context.update({'member': member_rec})

        # Primo chargement de la page
        if request.httprequest.method == 'GET':
            try:
                context['image_base64'] = website_tools.image.get_default_partner_image(member_rec)
            except IOError:
                raise ValueError("Non-image binary fields can not be converted to HTML")
            except Exception:  # image.verify() throws "suitable exceptions", I have no idea what they are
                raise ValueError("Invalid image content")

            return request.render('partner_type_foyer.cru_foyer_member', context)

        post, errors, errors_messages = self._validate_form(post, member_rec)
        context.update({
            'error': errors,
            'error_message': errors_messages,
            'post': post
        })

        if errors or errors_messages:
            # Affichage du formulaire avec ses erreurs
            return request.render('partner_type_foyer.cru_foyer_member', context)

        try:
            # If no errors, create or update partner record
            if post.get('image_base64') and post['image_base64'].startswith('data:'):
                post['image_base64'] = post['image_base64'].split(',')[1]
            post_values = website_tools.partner.prepare_fields(post)
            post_values = website_tools.partner.map_dictionary(
                post_values, MEMBER_MODEL_FIELD, {'image_base64': 'image'})
            # Mode édition
            if member_id:
                member_rec.write(post_values)
            # Mode création
            else:
                # On créer le nouveau membre
                new_member = member_rec.create(post_values)
                new_member.garant_workflow = 'initial'
                # On met l'adresse en "validée" si elle est identique
                if new_member.better_contact_address == user.partner_id.better_contact_address:
                    new_member.address_workflow = 'validated'
                # On rajoute le membre dans les dépendants du responsable
                user.partner_id.write({'dependant_ids': [(4, new_member.id)]})
                # Création de la relation avec le foyer
                relation_value = {'foyer_id': foyer.id,
                                  'partner_id': new_member.id,
                                  'begin_date': datetime.today().strftime(tools.DEFAULT_SERVER_DATE_FORMAT)}
                request.env['horanet.relation.foyer'].sudo().create(relation_value)
        except ValidationError as vex:
            request.env.cr.rollback()
            context.update({'error_message': vex.name.split('\n')})
            return request.render('partner_type_foyer.cru_foyer_member', context)
        except Exception as e:
            # S'assurer du rollback en cas d'erreur (non géré en frontend)
            e.args = ('Catching exception to force cursor rollback',)
            request.env.cr.rollback()
            raise

        return request.redirect(redirect)

    def _validate_form(self, values, partner):
        """
        Validate the values of the form.

        :param values: values of the post
        :param partner: the partner to edit
        :return: errors if any
        """
        errors = dict()
        errors_messages = []

        # Récupération de l'image sélectionné pour l'ajouter au post (pour affichage/enregistrement)
        if values.get('input_avatar'):
            image_base64, error_img = website_tools.image.get_base64_img_avatar_from_file(values['input_avatar'])

            if error_img:
                errors_messages.append(error_img)
            else:
                # Garder l'image précédente en cas d'erreur
                values['image_base64'] = image_base64
                values['has_custom_image'] = True

        # Validation des données du formulaire
        validation_errors, validation_errors_messages = website_tools.partner. \
            form_validate(values, is_company=False, validate_address=True)

        errors.update(validation_errors)
        errors_messages.extend(validation_errors_messages)

        return values, errors, errors_messages
