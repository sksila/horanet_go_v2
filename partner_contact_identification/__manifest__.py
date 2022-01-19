{
    # Module name in English
    'name': "Partner Contact Identification",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.11.20',
    # Short description (with keywords)
    'summary': "Module de gestion des supports d'identification",
    'author': "Horanet",
    'description': "no warning",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    'category': 'Other',
    #
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'website_portal',

        # --- External --- #

        # --- Horanet --- #
        'horanet_web',
        'horanet_go',
        'partner_contact_personal_information',
        'partner_contact_second_names',
    ],
    # always loaded
    'css': [],
    'qweb': [],
    # list of XML files with data that will load to DB at moment when you install module
    'init_xml': [],
    # list of XML files with data that will load to DB at moment when you install or update module.
    'update_xml': [],
    # List of data files which must always be installed or updated with the module.
    # A list of paths from the module root directory
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',

        'data/data.xml',

        'templates/portal_my_mediums.xml',

        'views/area_view.xml',
        'views/technology_view.xml',
        'views/mapping_view.xml',
        'views/medium_type_view.xml',
        'views/medium_view.xml',
        'views/assignation_view.xml',
        'views/tag_view.xml',
        'views/menu_view.xml',
        'views/inherited_partner_view.xml',
        'views/web_assets_backend.xml',
        'views/inherited_collectivity_config_settings_view.xml',

        'wizards/wizard_create_medium_view.xml',
        'wizards/wizard_deactivate_medium_view.xml',
        'wizards/wizard_create_identification_view.xml',

        'data/sequence_tag.xml',
        'data/config.xml',
        'data/report_paperformat.xml',

        'reports/medium_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': False,
    'auto_install': False,
    # permet d'installer automatiquement le module si toutes ses dépendances sont installés
    # -default value set is False
    # -If false, the dependent modules are not installed if not installed prior to the dependent module.
    # -If True, all corresponding dependent modules are installed at the time of installing this module.
    'installable': True
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
