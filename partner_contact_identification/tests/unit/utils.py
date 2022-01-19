# -*- coding: utf-8 -*-


def create_area(env, name):
    return env['partner.contact.identification.area'].create({
        'name': 'Area1'
    })


def create_technology(env, name):
    return env['partner.contact.identification.technology'].create({
        'name': 'Tech1',
        'code': 'Tech1'
    })


def create_mapping(env, tech_name, area_name, mapping=None):
    mapping_obj = env['partner.contact.identification.mapping']

    tech = env['partner.contact.identification.technology'].search([
        ('name', '=', tech_name)
    ])

    if not tech:
        tech = env['partner.contact.identification.technology'].create({
            'name': tech_name,
            'code': tech_name,
        })

    area = env['partner.contact.identification.area'].create({
        'name': area_name
    })

    values = {
        'mapping': 'csn',
        'technology_id': tech.id,
        'area_id': area.id,
    }

    if mapping:
        values['mapping'] = mapping

    return mapping_obj.create(values)


def create_tag(env, values={}):
    default_values = {
        'number': '1234567890',
        'mapping_id': env.ref('partner_contact_identification.mapping_mifare_csn_horanet').id,
    }

    default_values.update(values)

    return env['partner.contact.identification.tag'].create(default_values)


def create_partner(env, name):
    partner_obj = env['res.partner']

    return partner_obj.create({
        'name': name
    })


def create_assignation(env, values):
    return env['partner.contact.identification.assignation'].create(values)
