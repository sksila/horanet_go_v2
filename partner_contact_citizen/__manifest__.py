{
    # Module name in English
    'name': "Partner Contact Citizen",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.03.02',
    # Short description (with keywords)
    'summary': """Gestion des citoyens""",
    # Description with metadata (in french)
    'description': """no warning""",
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

        # --- External --- #
        'partner_firstname',

        # --- Horanet --- #
        'horanet_go',  # pour les menus et catégories de partner
        'better_address',
        'partner_contact_personal_information',
        'web_fields_masks',
        'horanet_web',  # pour agrandir les vues partner
        # 'horanet_go', liée à horanet_location/horanet_web

    ],
    # always loaded
    'qweb': [
    ],
    # list of XML files with data that will load to DB at moment when you install module
    'init_xml': [],
    # list of XML files with data that will load to DB at moment when you install or update module.
    'update_xml': [],
    # List of data files which must always be installed or updated with the module.
    # A list of paths from the module root directory
    'data': [
        'security/groups.xml',

        'templates/web_assets_backend.xml',

        'views/inherited_partner_view.xml',
        'views/inherited_res_country_view.xml',
        'views/partner_citizen_view.xml',
        'views/custom_partner_citizen_form_view.xml',
        'views/partner_horanet_go_view.xml',
        'views/custom_horanet_go_partner_form_view.xml',

        'views/menu.xml',
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
    'post_init_hook': 'post_init_hook',
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
