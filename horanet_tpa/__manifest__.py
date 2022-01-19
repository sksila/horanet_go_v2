{
    # Module name in English
    'name': "Horanet TPA",
    # Version, "odoo.min.yy.m.d"
    'version': '11.0.18.12.21',
    # Short description (with keywords)
    'summary': "Manage TPA horanet custom connector	Ne devrait jamais être installé directement",
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
        'python': ['uuid', 'threading', 'time', 'psycopg2']
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'base_automation',

        # --- External --- #

        # --- Horanet --- #
        'horanet_go',
        'partner_merge',
        'partner_type_foyer',
        'partner_contact_identification',
    ],
    # always loaded
    'css': [],
    'qweb': [],
    # list of XML files with data that will load to DB at moment when you install module
    'init_xml': [],
    # list of XML files with data that will load to DB at moment when you install or update module.
    'update_xml': [],
    # List of data files which must always be installed or updated with the module. A list of paths from the
    # module root directory
    'data': [
        'security/ir.model.access.csv',
        'views/inherited_partner_view.xml',
        'views/tpa_synchronization_status_view.xml',
        'views/tpa_synchronization_merge_view.xml',
        'wizards/wizard_import_data_synchro_view.xml',
        'views/menu.xml',
        'views/tpa_config_settings_view.xml',
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
    'installable': True
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
