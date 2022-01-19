from datetime import datetime

from openerp import _, tools
from openerp.exceptions import ValidationError
from openerp.http import request
from odoo.addons.partner_contact_citizen.tools import check_phone_number
from odoo.tools import safe_eval

from . import address


def form_validate(data, is_company=False, validate_address=True, user=False):
    """
    Add errors and the associated message in the dictionary if there is something wrong.

    :param data: data of the form
    :param is_company: if the data is for a company or a normal partner
    :param validate_address: set to true if we want address validation
    :return: error and associated message
    """
    error = dict()
    error_message = []

    # Si on veut valider l'adresse
    if validate_address:
        error_address, error_message_address = address.validate(data, False)
        error.update(error_address)
        error_message.extend(error_message_address)

    # Si on met une adresse de facturation en plus
    if data.get('has_invoice_address', False):
        error_address, error_message_address = address.validate(data, 'invoice')
        error.update(error_address)
        error_message.extend(error_message_address)

    # Si on met une adresse de livraison en plus
    if data.get('has_shipping_address', False):
        error_address, error_message_address = address.validate(data, 'shipping')
        error.update(error_address)
        error_message.extend(error_message_address)

    if data.get('birthdate_date'):
        try:
            datetime.strptime(data['birthdate_date'], request.env['res.lang'].get_date_format()).date()
        except ValueError:
            error['birthdate_date'] = 'error'
            error_message.append(_("Birthdate is incorrect"))

    # Traitement des champs spécifiques à une personne
    if not is_company:
        form_validate_not_company(data, error, error_message)

    # Traitement des champs spécifiques à une entreprise
    if is_company:
        form_validate_company(data, error, error_message, user)

    # email validation
    if not tools.single_email_re.match(data.get('email', '')):
        error['email'] = 'error'
        error_message.append(
            _("Incorrect email ! Please enter a valid email address."))

    form_validate_phone_mobile(data, is_company, error, error_message)

    # generic error message for empty required fields
    if [err for err in error.values() if err == 'missing']:
        error_message.append(_("Some required fields are empty."))

    return error, error_message


def form_validate_phone_mobile(data, is_company, error, error_message):
    # Phone validation
    phone = data.get('phone')
    mobile = data.get('mobile')
    country_model = request.env['res.country']

    if phone:
        phone = data['phone'].replace(' ', '')
        country_phone = data.get('country_phone')
        if country_phone:
            country_phone = country_model.browse(int(country_phone))
            check_phone_number.validation_phone_number(phone, country_phone.phone_code, country_phone.national_prefix,
                                                       error, error_message)

    if mobile and not is_company:
        mobile = data['mobile'].replace(' ', '')
        country_mobile = data.get('country_mobile')
        if country_mobile:
            country_mobile = country_model.browse(int(country_mobile))
            check_phone_number.validation_mobile_number(mobile, country_mobile.phone_code, country_mobile.mobile_prefix,
                                                        error, error_message)
    if not phone and not mobile:
        error_message.append(_("A phone or a mobile phone is required"))


def form_validate_not_company(data, error, error_message):
    if not data.get('title'):
        error['title'] = 'error'
        error_message.append(_("Title is missing"))
    if not data.get('lastname'):
        error['lastname'] = 'missing'
        error_message.append(_("Lastname is missing"))
    if not data.get('firstname'):
        error['firstname'] = 'missing'
        error_message.append(_("Firstname is missing"))
    # Validation quotient familial
    if data.get('quotient_fam', False):
        if not data.get('quotient_fam', False).isnumeric():
            error['quotient_fam'] = 'error'
            error_message.append(_("Enter a valid family quotient."))


def form_validate_company(data, error, error_message=list(), user=False):
    # As we now have a company form that is available for collectivities and associations
    # we can't make those fields required. Need to rewrite this in another way.

    # We make the attribute required switchable but that not resolve the first problem. To solve it we need to rewrite
    # the method to define a pro partner (is a company with siret, vat number, a associations without siret or vat
    # number, a physical partner, etc...)

    icp_model = request.env['ir.config_parameter'].sudo()

    required_vat_number = safe_eval(icp_model.get_param(
        'horanet_website_account.required_vat_number', 'False'
    ))
    required_ape_code = safe_eval(icp_model.get_param(
        'horanet_website_account.required_ape_code', 'False'
    ))
    required_siret_code = safe_eval(icp_model.get_param(
        'horanet_website_account.required_siret_code', 'False'
    ))

    if not data.get('vat_number') and required_vat_number:
        error['vat_number'] = 'missing'
    if not data.get('ape_code') and required_ape_code:
        error['ape_code'] = 'missing'
    if not data.get('siret_code') and required_siret_code:
        error['siret_code'] = 'missing'
    elif data.get('siret_code'):
        # Siret / Siren validation
        siret_code = data['siret_code'].replace(' ', '')
        if not siret_code.isnumeric() or (len(siret_code) != 9 and len(siret_code) != 14):
            error['siret_code'] = 'error'
            error_message.append(_('Enter a valid SIRET or SIREN number.'))

    if not data.get('title') and user and not user.partner_id.category_id:
        error['company_title'] = 'missing'
    if not data.get('name'):
        error['name'] = 'missing'


def prepare_fields(data):
    """
    Create new address related data (street, street number, ...) if needed and check the address location.

    :param data: data of the form
    :return: updated_values, values of the form updated after check
    """
    updated_values = data

    # détection du type d'adresse (française ou autre)
    if not data.get('country_id'):
        raise ValidationError('Country id not found')

    # Pour le département
    updated_values['state_id'] = request.env['res.city'].sudo().browse(int(data['city_id'])).country_state_id.id

    # Pour le code postal
    updated_values['zip_id'] = request.env['res.zip'].sudo().search([('name', '=', data['zipcode'])], limit=1).id

    # Création d'un numéro de rue si il n'existe pas
    if not data.get('street_number_id') and data.get('street_number'):
        sanitize_name = address.get_formatted_street_number(data.get('street_number'))
        street_number_model = request.env['res.street.number'].sudo()
        if sanitize_name:
            search = street_number_model.search([('name', '=ilike', sanitize_name)], limit=1)
            if search:
                updated_values['street_number_id'] = search[0].id
            else:
                new_street_number = street_number_model.create({'name': sanitize_name})
                updated_values['street_number_id'] = new_street_number.id

    # Création d'une nouvelle rue si case cochée
    if data.get('create_new_street') and data.get('new_street'):
        street_model = request.env['res.street'].sudo()
        search = street_model.search([('name', '=', data['new_street']),
                                      ('city_id.id', '=', int(data['city_id']))], limit=1)
        if not search:
            new_street = street_model.create(
                {'name': data['new_street'], 'city_id': int(data['city_id'])})
            updated_values['street_id'] = new_street.id
        else:
            updated_values['street_id'] = search.id

    if not data.get('birthdate_date'):
        updated_values['birthdate_date'] = False
    else:
        date_format = request.env['res.lang'].get_date_format()
        updated_values['birthdate_date'] = datetime.strptime(data['birthdate_date'], date_format).date()

    return updated_values


def map_dictionary(origin, keys_list, keys_mapping=None):
    u"""
    Permet de filtrer et mapper les clés d'un dictionnaire.

    :param origin: dictionnaire d'origin à mapper
    :param keys_list: liste des clés à filtrer
    :param keys_mapping: OPTIONNEL,liste des clés à mapper sous forme {'original_name':'new_name'}
    :return: dictionnaire filtré/mappé
    """
    if not keys_mapping:
        keys_mapping = {}
    return dict(
        ((k in keys_mapping and keys_mapping[k] or k, v) for k, v in origin.items()
         if k in keys_list or k in keys_mapping))
