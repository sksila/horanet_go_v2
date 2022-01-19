# -*- coding: utf-8 -*-
{
    'name': "Calypso AMC Import",
    'version': '10.0.18.10.17',
    'summary': "Import mediums and tags from a CSV file using AMC standard",
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
        'environment_waste_collect',  # Pour surcharge api ecopad
        'partner_contact_identification',
    ],
    'data': [
        'security/groups.xml',

        'data/data.xml',

        'wizards/import_calypso_amc_view.xml',

        'views/menu.xml'
    ],
    'installable': False
}
