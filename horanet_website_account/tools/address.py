import re

from openerp import _
from openerp.http import request


def is_protected_country(request, country_id):
    """
    Check if a country is in the protect countries list in the config.

    :param request: the request
    :param country_id: the id of the country
    :return: bool  True if country is protected
    """
    list_french_country = request.env['res.config.settings'].get_protected_countries_ids()
    country = request.env['res.country'].browse([country_id])
    return bool(country in list_french_country)


def get_formatted_street_number(string):
    """
    Format street number and check if it is one.

    001 -> 1
    13 bis / 13 Bis -> 13 bis
    :param string: contains the street number
    :return: formatted street number
    """
    formatted_street_number = None
    match = re.search(r'^[\s0]*([0-9]+)\s*([a-zA-Z]|[Bb]is|[Tt]er)?\s*$', string)
    if match:
        formatted_street_number = match.group(1)
        if match.group(2):
            formatted_street_number += ' ' + match.group(2)
    return formatted_street_number


def validate(data, prefix):
    """
    Check address data from the address form.

    :param data: fields of the address form
    :return: error list
    """
    error = dict()
    error_message = []
    prefix = prefix and str(prefix) + '_' or ''

    country_id = prefix + 'country_id'
    city_id = prefix + 'city_id'
    zipcode = prefix + 'zipcode'
    street_number = prefix + 'street_number'

    address_fields = [
        country_id,
        city_id,
        zipcode,
        street_number]

    # Validation
    for field_name in address_fields:
        if not data.get(field_name):
            error[field_name] = 'missing'

    # Street
    if not data.get(prefix + 'create_new_street') and not data.get(prefix + 'street'):
        error[prefix + 'street'] = 'missing'
    # Ne devrais pas arriver puisque le champs id est vide (javascript) si on ne sélectionne rien
    if not data.get(prefix + 'street_id') and data.get(prefix + 'street'):
        error[prefix + 'street'] = 'error'
        error_message.append(_('The street is not correctly set'))

    # New street
    if data.get(prefix + 'create_new_street') and not data.get(prefix + 'new_street'):
        error[prefix + 'new_street'] = 'missing'

    # street number validation
    # Ne devrais par arrivé car champs ID vide (javascript) si rien de sélectionné
    if data.get(prefix + 'street_number') and not data[prefix + 'street_number_id']:
        if not get_formatted_street_number(data[prefix + 'street_number']):
            error[prefix + 'street_number'] = 'error'
            error_message.append(_('Street number field is incorrectly formatted'))

    # generic error message for empty required fields
    if [err for err in error.values() if err == 'missing']:
        error_message.append(_("Address fields missing"))

    return error, error_message


def validate_invoice(data):
    """
    Check address data from the invoice address form.

    :param data: fields of the invoice address form
    :return: error list
    """
    error = dict()
    error_message = []
    address_fields = [
        'invoice_country_id',
        'invoice_city_id',
        'invoice_zipcode',
        'invoice_street_number']

    # Validation
    for field_name in address_fields:
        if not data.get(field_name):
            error[field_name] = 'missing'

    # Street
    if not data.get('invoice_create_new_street') and not data.get('invoice_street'):
        error['invoice_street'] = 'missing'
    # Ne devrais pas arriver puisque le champs id est vide (javascript) si on ne sélectionne rien
    if not data.get('invoice_street_id') and data.get('invoice_street'):
        error['invoice_street'] = 'error'
        error_message.append(_('The street is not correctly set'))

    # New street
    if data.get('invoice_create_new_street') and not data.get('invoice_new_street'):
        error['invoice_new_street'] = 'missing'

    # street number validation
    # Ne devrais par arrivé car champs ID vide (javascript) si rien de sélectionné
    if data.get('invoice_street_number') and not data['invoice_street_number_id']:
        if not get_formatted_street_number(data['invoice_street_number']):
            error['invoice_street_number'] = 'error'
            error_message.append(_('Street number field is incorrectly formatted'))

    # generic error message for empty required fields
    if [err for err in error.values() if err == 'missing']:
        error_message.append(_("Address fields missing"))

    return error, error_message


def validate_shipping(data):
    """
    Check address data from the shipping address form.

    :param data: fields of the shipping address form
    :return: error list
    """
    error = dict()
    error_message = []
    address_fields = [
        'shipping_country_id',
        'shipping_city_id',
        'shipping_zipcode',
        'shipping_street_number']

    # Validation
    for field_name in address_fields:
        if not data.get(field_name):
            error[field_name] = 'missing'

    # Street
    if not data.get('shipping_create_new_street') and not data.get('shipping_street'):
        error['shipping_street'] = 'missing'
    # Ne devrais pas arriver puisque le champs id est vide (javascript) si on ne sélectionne rien
    if not data.get('shipping_street_id') and data.get('shipping_street'):
        error['shipping_street'] = 'error'
        error_message.append(_('The street is not correctly set'))

    # New street
    if data.get('shipping_create_new_street') and not data.get('shipping_new_street'):
        error['shipping_new_street'] = 'missing'

    # street number validation
    # Ne devrais par arrivé car champs ID vide (javascript) si rien de sélectionné
    if data.get('shipping_street_number') and not data['shipping_street_number_id']:
        if not get_formatted_street_number(data['shipping_street_number']):
            error['shipping_street_number'] = 'error'
            error_message.append(_('Street number field is incorrectly formatted'))

    # generic error message for empty required fields
    if [err for err in error.values() if err == 'missing']:
        error_message.append(_("Address fields missing"))

    return error, error_message


def create_invoice_address(partner_id, data):
    """
    Create the invoice address (partner).

    :param partner_id: the parent
    :param data: address data
    """
    # Pour le département
    data['invoice_state_id'] = request.env['res.city'].sudo().browse(int(data['invoice_city_id'])).country_state_id.id

    # Pour le code postal
    data['invoice_zip_id'] = request.env['res.zip'].sudo().search([('name', '=', data['invoice_zipcode'])], limit=1).id

    # Création d'une nouvelle rue si case cochée
    if data.get('invoice_create_new_street') and data.get('invoice_new_street'):
        street_model = request.env['res.street'].sudo()
        search = street_model.search([('name', '=', data['invoice_new_street']),
                                      ('city_id.id', '=', int(data['invoice_city_id']))], limit=1)
        if not search:
            new_street = street_model.create(
                {'name': data['invoice_new_street'], 'city_id': int(data['invoice_city_id'])})
            data['invoice_street_id'] = new_street.id
        else:
            data['invoice_street_id'] = search.id

    # Création d'un numéro de rue si il n'existe pas
    if not data.get('invoice_street_number_id') and data.get('invoice_street_number'):
        sanitize_name = get_formatted_street_number(data.get('invoice_street_number'))
        street_number_model = request.env['res.street.number'].sudo()
        if sanitize_name:
            search = street_number_model.search([('name', '=ilike', sanitize_name)], limit=1)
            if search:
                data['invoice_street_number_id'] = search[0].id
            else:
                new_street_number = street_number_model.create({'name': sanitize_name})
                data['invoice_street_number_id'] = new_street_number.id

    invoice_address = partner_id.child_ids.filtered(lambda r: r.type == 'invoice')
    # Si il n'y a pas encore d'adresse de facturation on la créer
    if not invoice_address:
        values = {'parent_id': partner_id.id,
                  'type': 'invoice',
                  'name': data.get('invoice_name'),
                  'street_number_id': data.get('invoice_street_number_id'),
                  'street_id': data.get('invoice_street_id'),
                  'street2': data.get('invoice_street2'),
                  'street3': data.get('invoice_street3'),
                  'city_id': data.get('invoice_city_id'),
                  'zip_id': data.get('invoice_zip_id'),
                  'state_id': data.get('invoice_state_id'),
                  'country_id': data.get('invoice_country_id')}

        request.env['res.partner'].create(values)
    # Sinon on la met à jour
    elif len(invoice_address) == 1:
        values = {'name': data.get('invoice_name'),
                  'street_number_id': data.get('invoice_street_number_id'),
                  'street_id': data.get('invoice_street_id'),
                  'street2': data.get('invoice_street2'),
                  'street3': data.get('invoice_street3'),
                  'city_id': data.get('invoice_city_id'),
                  'zip_id': data.get('invoice_zip_id'),
                  'state_id': data.get('invoice_state_id'),
                  'country_id': data.get('invoice_country_id')}
        invoice_address.write(values)


def create_shipping_address(partner_id, data):
    """
    Create the shipping address (partner).

    :param partner_id: the parent
    :param data: address data
    """
    # Pour le département
    data['shipping_state_id'] = request.env['res.city'].sudo().browse(int(data['shipping_city_id'])).country_state_id.id

    # Pour le code postal
    data['shipping_zip_id'] = request.env['res.zip'].sudo().search([('name', '=', data['shipping_zipcode'])],
                                                                   limit=1).id

    # Création d'une nouvelle rue si case cochée
    if data.get('shipping_create_new_street') and data.get('shipping_new_street'):
        street_model = request.env['res.street'].sudo()
        search = street_model.search([('name', '=', data['shipping_new_street']),
                                      ('city_id.id', '=', int(data['shipping_city_id']))], limit=1)
        if not search:
            new_street = street_model.create(
                {'name': data['shipping_new_street'], 'city_id': int(data['shipping_city_id'])})
            data['shipping_street_id'] = new_street.id
        else:
            data['shipping_street_id'] = search.id

    # Création d'un numéro de rue si il n'existe pas
    if not data.get('shipping_street_number_id') and data.get('shipping_street_number'):
        sanitize_name = get_formatted_street_number(data.get('shipping_street_number'))
        street_number_model = request.env['res.street.number'].sudo()
        if sanitize_name:
            search = street_number_model.search([('name', '=ilike', sanitize_name)], limit=1)
            if search:
                data['shipping_street_number_id'] = search[0].id
            else:
                new_street_number = street_number_model.create({'name': sanitize_name})
                data['shipping_street_number_id'] = new_street_number.id

    shipping_address = partner_id.child_ids.filtered(lambda r: r.type == 'delivery')
    # Si il n'y a pas encore d'adresse de livraison on la créer
    if not shipping_address:
        values = {'parent_id': partner_id.id,
                  'type': 'delivery',
                  'name': data.get('shipping_name'),
                  'street_number_id': data.get('shipping_street_number_id'),
                  'street_id': data.get('shipping_street_id'),
                  'street2': data.get('shipping_street2'),
                  'street3': data.get('shipping_street3'),
                  'city_id': data.get('shipping_city_id'),
                  'zip_id': data.get('shipping_zip_id'),
                  'state_id': data.get('shipping_state_id'),
                  'country_id': data.get('shipping_country_id')}

        request.env['res.partner'].create(values)
    # Sinon on la met à jour
    elif len(shipping_address) == 1:
        values = {'name': data.get('shipping_name'),
                  'street_number_id': data.get('shipping_street_number_id'),
                  'street_id': data.get('shipping_street_id'),
                  'street2': data.get('shipping_street2'),
                  'street3': data.get('shipping_street3'),
                  'city_id': data.get('shipping_city_id'),
                  'zip_id': data.get('shipping_zip_id'),
                  'state_id': data.get('shipping_state_id'),
                  'country_id': data.get('shipping_country_id')}
        shipping_address.write(values)
