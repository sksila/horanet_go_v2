{
    # Module name in English
    'name': "Horanet SignUp",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.9.12',
    # Short description (with keywords)
    'summary': "Modification du formulaire d'inscription pour y ajouter le nom et prénom",
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    'description': 'no warning',
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
        'auth_signup',
        'website',
        'portal',  # pour le wizard d'accès au portail

        # --- External --- #
        # OCA partner-contact
        'partner_firstname',
        'auth_signup_verify_email',

        # --- Horanet --- #
        'horanet_website',  # Nécessaire pour bénéficier des traductions JS
        'horanet_go',
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
        'data/auth_signup_data.xml',
        'data/ir_config_parameter.xml',
        'data/ir_cron.xml',
        'views/inherited_partner_view.xml',
        'views/inherited_collectivity_config_view.xml',
        'views/inherited_base_config_view.xml',
        'views/inherited_users_view.xml',

        'templates/inherited_auth_signup_login.xml',
        'templates/website_assets_frontend.xml',

        'wizards/inherited_portal_wizard_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
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
