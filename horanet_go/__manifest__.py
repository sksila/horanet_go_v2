{
    # Module name in English
    'name': "Horanet GO",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.6.6',
    # Short description (with keywords)
    'summary': "Contient les modèles de base d'une gestion de collectivité",
    # Description with metadata (in french)
    'description': "Application de gestion des collectivités",
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    'contributors': [
        'DIDENOT Adrien ',
    ],
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
        # 'base', liée à mail et web
        'mail',
        'web',  # modification traduction

        # --- External --- #
        'web_search_with_and',  # Use AND conditions on omnibar search When searching for records on same field.
        # 'disable_odoo_online',
        'website_odoo_debranding',  # Used to disable the odoo logo in front
        'web_advanced_search',  # To have a full search view to select the record in question
        # This module adds a checkbox to this list so multiple entries can be selected at once.
        'web_widget_many2many_tags_multi_selection',
        # Needaction counters in main menu. Show the sum of submenus (OCA web)
        # 'web_menu_navbar_needaction', # n'existe plus depuis la v9

        # --- Horanet --- #
        'horanet_web',  # Pour les outils de requête JSON
        'horanet_website',  # Pour l'affichage de la page de version
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
        'data/config.xml',
        'data/ir_module_category.xml',
        'data/partner_categories.xml',
        'data/sequences.xml',
        'data/partner_title.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',

        'views/collectivity_config_settings_view.xml',
        'views/horanet_module_view.xml',
        'views/subscription_category_partner_view.xml',
        'views/inherited_partner_view.xml',
        'views/inherited_partner_title_view.xml',

        'templates/page_version.xml',

        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'auto_install': False,
    # permet d'installer automatiquement le module si toutes ses dépendances sont installés
    # -default value set is False
    # -If false, the dependent modules are not installed if not installed prior to the dependent module.
    # -If True, all corresponding dependent modules are installed at the time of installing this module.
    'installable': True,
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    # method called after the first installation of this module
}
