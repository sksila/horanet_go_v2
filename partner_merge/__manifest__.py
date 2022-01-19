# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "Partner merge",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.17.2.9',
    # Short description (with keywords)
    'summary': 'Permet de fusionner des partenaires',
    'description': 'no_warning',
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Tools',
    #
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'crm',
        # --- External --- #

        # --- Horanet --- #
        'horanet_go',
        'partner_contact_citizen',
        'partner_contact_personal_information',
    ],
    # always loaded
    'qweb': [],
    # list of XML files with data that will load to DB at moment when you install module
    'init_xml': [],
    # list of XML files with data that will load to DB at moment when you install or update module.
    'update_xml': [],
    # List of data files which must always be installed or updated with the module.
    # A list of paths from the module root directory
    'data': [
        'security/groups.xml',

        'views/inherited_partner_views.xml',
        'views/inherited_collectivity_config_settings_view.xml',
        'views/duplicate_partner_view.xml',

        'wizards/inherited_base_partner_merge_view.xml',

        'views/menu.xml',
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
    'installable': True,
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
