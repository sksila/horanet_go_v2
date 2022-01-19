# -*- coding: utf-8 -*-

from odoo.addons.website_application.controllers.main import WebsiteApplications
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo import http, tools, _

from odoo.addons.horanet_website_account import tools as website_tools
from odoo.addons.horanet_website_account.controllers import company as company
from odoo.addons.horanet_website_account.controllers import main as partner_create

from datetime import datetime


class EnvironmentWebsiteApplications(WebsiteApplications):
    """We inherit this class to add the new type of request."""

    @http.route('/environment-support-rules', type="http", auth="public", website=True)
    def environment_support_rules(self):
        """To redirect to support rules page."""
        return request.render('environment_applications.environment_support_rules')

    def create_new_partner_foyer(self, values, user):
        """Create The new partner in a foyer.

        :param values: values of creation
        :param user: the user
        :return: the new partner record
        """
        partner_model = request.env['res.partner']
        foyers = user.foyer_relation_ids.filtered('is_valid').mapped('foyer_id')

        if values.get('input_avatar'):
            image_base64, error_img = website_tools.image.get_base64_img_avatar_from_file(
                values['input_avatar'])
            if error_img:
                raise ValidationError(error_img)
            else:
                # Garder l'image précédente en cas d'erreur
                values['image_base64'] = image_base64
                values['has_custom_image'] = True

        error_validation, error_message_validation = website_tools.partner. \
            form_validate(values, is_company=False, validate_address=True)
        if error_validation:
            raise ValidationError(_("For recipient creation:") + '\n- ' +
                                  '\n- '.join(error_message_validation))

        # If no errors, create or update partner record
        if values.get('image_base64') and values['image_base64'].startswith('data:'):
            values['image_base64'] = values['image_base64'].split(',')[1]

        post_values = website_tools.partner.prepare_fields(values)
        post_values = website_tools.partner.map_dictionary(post_values,
                                                           partner_create.PARTNER_MODEL_FIELD,
                                                           {'image_base64': 'image'})
        # On créer le nouveau membre
        new_member = partner_model.sudo().create(post_values)
        new_member.garant_workflow = 'initial'
        # On met l'adresse en "validée" si elle est identique
        if new_member.better_contact_address == user.partner_id.better_contact_address:
            new_member.address_workflow = 'validated'
        # On rajoute le membre dans les dépendants du responsable
        user.partner_id.write({'garant_ids': [(4, new_member.id)]})
        # Création de la relation avec le foyer
        relation_value = {'foyer_id': foyers[0].id,
                          'partner_id': new_member.id,
                          'begin_date': datetime.today().strftime(tools.DEFAULT_SERVER_DATE_FORMAT)}
        request.env['horanet.relation.foyer'].sudo().create(relation_value)

        return new_member

    def create_new_employee(self, values, user):
        """Create the new employee.

        :param values: values used for the creation
        :param user: the user
        :return: the new employee record
        """
        partner_model = request.env['res.partner']
        if values.get('input_avatar'):
            image_base64, error_img = website_tools.image.get_base64_img_avatar_from_file(
                values['input_avatar'])
            if error_img:
                raise ValidationError(error_img)
            else:
                # Garder l'image précédente en cas d'erreur
                values['image_base64'] = image_base64
                values['has_custom_image'] = True

        error_validation, error_message_validation = website_tools.partner. \
            form_validate(values, is_company=False, validate_address=False)
        if error_validation:
            raise ValidationError(_("For employee creation:") + '\n- ' +
                                  '\n- '.join(error_message_validation))

        # If no errors, create or update partner record
        if values.get('image_base64') and values['image_base64'].startswith('data:'):
            values['image_base64'] = values['image_base64'].split(',')[1]

        employee_values = website_tools.partner.map_dictionary(values, company.MEMBER_MODEL_FIELD,
                                                               {'image_base64': 'image'})
        # On créer le nouvel employé
        # On le met en type "contact"
        employee_values['type'] = 'contact'
        new_employee = partner_model.sudo().create(employee_values)
        new_employee.garant_workflow = 'initial'
        # On rajoute l'employé dans l'entreprise
        user.partner_id.write({'child_ids': [(4, new_employee.id)]})
        return new_employee
