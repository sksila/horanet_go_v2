# -*- coding: utf-8 -*-
{
    'name': "environment_waste_collect_cardmaker_export",

    'summary': """Allow usage of license plates when using cardmaker export wizard""",

    'description': """Allow usage of license plates when using cardmaker export wizard""",

    'author': "Horanet",
    'website': "https://www.horanet.com",

    'category': 'Uncategorized',
    'version': '10.0.18.05.29',

    'depends': [
        'base',
        'environment_waste_collect',
        'cardmaker_export',
        'environment_applications'
    ],

    'auto_install': False,

    'data': [
        'data/application_informations.xml',
        'data/action_servers.xml',

        'views/inherited_export_view.xml',
        'wizards/inherited_export_partners_view.xml',
    ],
}
