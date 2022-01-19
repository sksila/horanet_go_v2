import logging

from odoo.addons.horanet_website_account import tools as website_tools
from odoo.addons.portal.controllers.portal import CustomerPortal

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)

MEMBER_MODEL_FIELD = [
    'firstname', 'lastname', 'firstname2', 'lastname2',
    'title', 'phone', 'mobile', 'image', 'email',
    'has_custom_image', 'function',
]


class WebsiteAccountCompany(CustomerPortal):
    def _prepare_portal_layout_values(self):
        """Delete the My Company link in the menu if the option is not activated."""
        context = super(WebsiteAccountCompany, self)._prepare_portal_layout_values()

        icp_model = request.env['ir.config_parameter'].sudo()
        manage_employees = safe_eval(icp_model.get_param(
            'horanet_website_account.manage_employees', 'False'
        ))

        context.update({
            'manage_employees': manage_employees,
        })
        return context


class WebsiteAccountMyCompany(http.Controller):
    """Class of the controllers of company employees."""

    @http.route(['/my/company'], type='http', auth='user', website=True)
    def company(self):
        """Show employees."""
        user = request.env.user
        # We do not allow the user to got to this url if the option is not activated
        icp_model = request.env['ir.config_parameter'].sudo()
        manage_employees = safe_eval(icp_model.get_param(
            'horanet_website_account.manage_employees', 'False'
        ))

        qweb_context = {
            'user': user,
            'partner': user.partner_id,
        }

        if manage_employees:
            return request.render('horanet_website_account.my_company', qweb_context)
        else:
            return request.redirect('/my/home')

    @http.route(['/my/company/delete/<int:employee_id>'], type='http', auth='user', website=True)
    def delete_employee(self, employee_id=None):
        """Delete an employee."""
        user = request.env.user

        qweb_context = {
            'user': user,
            'partner': user.partner_id,
        }

        employee_rec = request.env['res.partner'].browse([employee_id])
        # On vérifie que l'employé existe et qu'il appartient bien à la société
        if employee_rec and employee_rec.parent_id.id == user.partner_id.id:
            employee_rec.sudo().unlink()

        return request.render('horanet_website_account.my_company', qweb_context)

    @http.route(['/my/company/create/employee',
                 '/my/company/edit/employee/<int:employee_id>'],
                type='http', auth='user', website=True, method=['POST', 'GET'])
    def create_employee(self, redirect='/my/company', employee_id=None, *args, **post):
        """Create and edit employees."""
        # Ajouter le contexte courant à qweb
        context = dict(request.context)
        user = request.env.user
        partner_model = request.env['res.partner']
        context.update({
            'user': user,  # Utilisateur courant
            'error': {},  # Liste des champs en erreur (avec message)
            'error_message': [],  # Liste des messages d'erreur générique
            'partner_titles': request.env['res.partner.title'].search([]),
            'mode_creation': not bool(employee_id),  # Pour différencier le mode création/édition
            'post': post,  # Data du PostBack pour conservation de saisi
            'redirect': redirect  # Chemin de redirection
        })

        # Création de l'objet partner
        if employee_id:
            # Mode edition
            partner_model.check_access_rights('write')
            employee_rec = partner_model.browse([employee_id])
        else:
            # Mode création
            partner_model.check_access_rights('create')
            default_val = partner_model.default_get(partner_model.fields_get())
            employee_rec = partner_model.new(default_val)

        context.update({'partner': employee_rec})

        # Primo chargement de la page
        if request.httprequest.method == 'GET':
            try:
                context['image_base64'] = website_tools.image.get_default_partner_image(employee_rec)
            except IOError:
                raise ValueError("Non-image binary fields can not be converted to HTML")
            except Exception:  # image.verify() throws "suitable exceptions", I have no idea what they are
                raise ValueError("Invalid image content")

            return request.render('horanet_website_account.create_employee', context)

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
                    post['image_base64'] = image_base64
                    post['has_custom_image'] = True

            # Validation des données du formulaire
            error_validation, error_message_validation = website_tools.partner. \
                form_validate(post, is_company=False, validate_address=False)
            error.update(error_validation)
            error_message.extend(error_message_validation)
            context.update({'error': error, 'error_message': error_message})
            context['post'].update(post)

            if error or error_message:
                # Affichage du formulaire avec ses erreurs
                return request.render('horanet_website_account.create_employee', context)
            else:
                try:
                    # If no errors, create or update partner record
                    if post.get('image_base64') and post['image_base64'].startswith('data:'):
                        post['image_base64'] = post['image_base64'].split(',')[1]
                    post_values = website_tools.partner.map_dictionary(post, MEMBER_MODEL_FIELD,
                                                                       {'image_base64': 'image'})
                    # Mode édition
                    if employee_id:
                        employee_rec.sudo().write(post_values)
                    # Mode création
                    else:
                        # On créer le nouvel employé
                        # On le met en type "contact"
                        post_values['type'] = 'contact'
                        new_employee = employee_rec.sudo().create(post_values)
                        new_employee.garant_workflow = 'initial'
                        # On rajoute l'employé dans l'entreprise
                        user.partner_id.write({'child_ids': [(4, new_employee.id)]})
                except ValidationError as vex:
                    request.env.cr.rollback()
                    context.update({'error_message': vex.value.split('\n')})
                    return request.render('horanet_website_account.create_employee', context)
                except Exception as e:
                    # S'assurer du rollback en cas d'erreur (non géré en frontend)
                    e.args = ('Catching exception to force cursor rollback',)
                    request.env.cr.rollback()
                    raise

        return request.redirect(redirect)
