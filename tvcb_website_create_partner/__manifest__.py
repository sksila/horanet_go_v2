# -*- coding: utf-8 -*-
{
    'name': 'TVCB Create Parner Website Page',

    'summary': """Allow creation of partner from a simple page.""",

    'description': "no warning",

    'author': 'Horanet',
    'website': 'www.horanet.com',
    'license': 'AGPL-3',

    'category': 'Website',
    'version': '10.0.17.5.22',

    'depends': [
        'base',
        'website',

        'better_address',
        'horanet_auth_signup',
        'horanet_tpa_aquagliss',
        'partner_contact_citizen',
        'partner_type_foyer',
    ],

    'data': [
        'templates/create_partner.xml',
        'templates/website_assets_frontend.xml',
    ],
    'installable': False,
}
