# -*- coding: utf-8 -*-
{
    'name': "Cardmaker Export",
    'version': '10.0.17.11.29',
    'summary': "Export list of partners that don't have active medium",
    'author': "Horanet",
    'description': "no warning",
    'website': "http://www.horanet.com/",
    'category': 'Other',
    'external_dependencies': {
        'python': []
    },
    'depends': [
        # --- Odoo --- #

        # --- External --- #

        # --- Horanet --- #
        'partner_contact_identification',
        'better_address',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',

        'wizards/export_partners_view.xml',

        'views/export.xml',
        'views/menu.xml'
    ],
    'installable': False
}
