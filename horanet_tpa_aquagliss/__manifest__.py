# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "Horanet TPA Aquagliss",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.02.22',
    # Short description (with keywords)
    'summary': "Manage TPA between Odoo and Aquagliss systems",
    # Description with metadata (in french)
    'description': "no_warning",
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Human Resources',
    #
    'external_dependencies': {
        'python': [
            'simplejson',
            'uuid',
            'requests'
        ]
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #

        # --- External --- #

        # --- Horanet --- #
        'horanet_auth_signup',
        'horanet_tpa',
        'website_application',
    ],
    # always loaded
    'css': [],
    'qweb': [],
    # list of XML files with data that will load to DB at moment when you install module
    'init_xml': [],
    # list of XML files with data that will load to DB at moment when you install or update module.
    'update_xml': [],
    # List of data files which must always be installed or updated with the module. A list of paths from
    # the module root directory
    'data': [
        'security/groups.xml',
        'data/settings.xml',
        'data/actions.xml',
        'data/actions_server.xml',
        'views/inherited_partner_view.xml',
        'views/inherited_tpa_config_settings_view.xml',
        'views/inherited_tpa_synchronization_merge_view.xml',
        'views/inherited_tpa_synchronization_status_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': False,
    # permet d'installer automatiquement le module si toutes ses dépendances sont installés
    'auto_install': False,
    # -default value set is False
    # -If false, the dependent modules are not installed if not installed prior to the dependent module.
    # -If True, all corresponding dependent modules are installed at the time of installing this module.
    'installable': False,
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
