import logging
import re

from odoo import SUPERUSER_ID, api, tools


def post_init_hook(cr, registry):
    """Post-install script.

    Because 'street', 'city', 'zip', 'street2' are now computed fields based on
    the new model of better address, to keep the existing address data, this method is used to create
    the new address model, and trigger the recompute of the base fields.
    """
    _logger = logging.getLogger('odoo.addons.better_address')
    _logger.info('Migrating existing old address to better address')

    env = api.Environment(cr, SUPERUSER_ID, {})
    # get all partner needing update
    partners_to_update = env['res.partner'].with_context(active_test=False).search(
        [
            '|',
            '|',
            ('city', '!=', False),
            ('zip', '!=', False),
            '|',
            ('street', '!=', False),
            ('street2', '!=', False),
        ])

    # create res.city
    for partner in partners_to_update.filtered('city'):
        with tools.ignore(Exception):
            partner.city_id = get_or_create_city(env, partner.city, partner.state_id, partner.country_id).id

    # deleting the zip of partner without city (trigger recompute)
    for partner in partners_to_update.filtered(lambda p: not p.city_id and p.zip):
        with tools.ignore(Exception):
            partner.zip = None

    # creating zip records
    for partner in partners_to_update.filtered(lambda p: p.city_id and p.zip):
        with tools.ignore(Exception):
            partner.zip_id = get_or_create_zip(env, partner.zip, partner.city_id).id

    # # creating res.street2 records
    # for partner in partners_to_update.filtered('street2'):
    #     with tools.ignore(Exception):
    #         partner.street2_id = get_or_create_street_2(env, partner.street2).id

    # deleting the street of partner without city
    for partner in partners_to_update.filtered(lambda p: not p.city_id and p.street):
        with tools.ignore(Exception):
            partner.street = None

    # creating the street-number rec and street by splitting the partner.street
    for partner in partners_to_update.filtered(lambda p: p.city_id and p.street):
        with tools.ignore(Exception):
            street_number, street = split_street_string(partner.street)
            if street:
                partner.street_id = get_or_create_street(env, street, partner.city_id).id
            if street_number:
                partner.street_number_id = get_or_create_street_number(env, street_number).id


def get_or_create_city(env, name, state_id, country_id):
    city_model = env['res.city']
    domain = [('name', '=ilike', name)]
    if state_id and state_id.id:
        domain.append(('country_state_id', '=', state_id.id))
    elif country_id and country_id.id:
        domain.append(('country_id', '=', country_id.id))
    city_rec = city_model.search(domain, limit=1)
    if not city_rec:
        city_rec = city_model.create({'name': name,
                                      'country_state_id': state_id and state_id.id,
                                      'country_id': country_id and country_id.id})
    return city_rec


def get_or_create_zip(env, name, city_rec):
    zip_model = env['res.zip']
    zip_rec = zip_model.search([('name', '=ilike', name)], limit=1)
    if not zip_rec:
        zip_rec = zip_model.create({
            'name': name,
            'city_ids': [(4, city_rec.id)]})
    elif city_rec.id not in zip_rec.city_ids.ids:
        zip_rec.city_ids = [(4, city_rec.id)]
    return zip_rec


def get_or_create_street_2(env, name):
    street2_model = env['res.street2']
    street2_rec = street2_model.search([('name', '=ilike', name)], limit=1)
    if not street2_rec:
        street2_rec = street2_model.create({'name': name})
    return street2_rec


def get_or_create_street(env, name, city_rec):
    street_model = env['res.street']
    street_rec = street_model.search([('name', '=ilike', name), ('city_id', '=', city_rec.id)], limit=1)
    if not street_rec:
        street_rec = street_model.create({
            'name': name,
            'city_id': city_rec.id})
    return street_rec


def get_or_create_street_number(env, name):
    street_number_model = env['res.street.number']
    street_number_rec = street_number_model.search([('name', '=ilike', name)], limit=1)
    if not street_number_rec:
        street_number_rec = street_number_model.create({'name': name})
    return street_number_rec


def split_street_string(street_str):
    """Split street string in street number and street name.

    voir
    Examples
        001 -> ('1',None)
        13 bis / 13 Bis -> ('13 bis',None)
        14 rue chauvelot -> ('14','rue chauvelot')

    :param street_str: contains the street number
    :return: The street number and/or the street name
    :rtype: Tuple('str','str')
    """
    result = [None, None]
    match = re.search(r'^[\s0]*([0-9]*)\s*([Bb]is|[Tt]er|[a-zA-Z]\s)?\s*(.*)\s*$', street_str)
    if match:
        if match.group(1):
            result[0] = match.group(1)
            if match.group(2):
                result[0] += ' ' + match.group(2)
        if match.group(3):
            result[1] = match.group(3)
    return tuple(result)
