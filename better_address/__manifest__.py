{
    # Module name in English
    'name': "Better address",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.17.1.17',
    # Short description (with keywords)
    'summary': "Enhanced zip/address management system",
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Human Resources',
    #
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'base',
        'web',

        # --- External --- #
        'base_search_fuzzy',  # OCA module de gestion des recherche "fuzzy" pour le merge d'adresses (entre autre)

        # --- Horanet --- #
        'horanet_go',
        'horanet_web',  # for the force field dirty trick and api
    ],
    # always loaded
    'qweb': [],
    # list of XML files with data that will load to DB at moment when you install module
    'init_xml': [],
    # list of XML files with data that will load to DB at moment when you install or update module.
    'update_xml': [],
    # List of data files which must always be installed or updated with the module.
    #  A list of paths from the module root directory
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',

        'wizards/wizard_deletion.xml',
        'wizards/wizard_import_data_fr_view.xml',
        'wizards/wizard_merge_city_view.xml',
        'wizards/wizard_merge_street_view.xml',

        'views/res_city_view.xml',
        'views/inherited_res_country_state_view.xml',
        'views/inherited_res_country_view.xml',
        'views/inherited_company_view.xml',
        'views/inherited_partner_view.xml',
        'views/res_zip_view.xml',
        'views/res_street_view.xml',
        'views/res_street_number_view.xml',
        'views/inherited_collectivity_config_view.xml',
        'views/menu.xml',
        'templates/web_assets_backend.xml',

        'data/states.xml',
        'data/settings.xml',
        'data/trigram_index.xml',
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
    'installable': True,
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
    'post_init_hook': 'post_init_hook',
    # method called after the first installation of this module
}
