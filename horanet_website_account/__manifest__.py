{
    # Module name in English
    'name': "Horanet Website Account",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.9.12',
    # Short description (with keywords)
    'summary': "Amélioration du portail client",
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    'description': "no warning",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Website',
    #
    'external_dependencies': {
        'python': [
            'PIL',  # Pillow
            'magic',  # python-magic
            'phonenumbers'
        ]
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'portal',
        'auth_signup',

        # --- External --- #
        # --- Horanet --- #
        'better_address',
        'partner_contact_citizen',
        'partner_contact_second_names',
        'partner_contact_personal_information',
        'horanet_website',
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
        'templates/website_assets_frontend.xml',
        'templates/partner_address_templates.xml',
        'templates/partner_image_templates.xml',
        'templates/partner_informations_templates.xml',
        'templates/page_my_account.xml',
        'templates/inherited_portal_templates.xml',
        'templates/page_my_company.xml',
        'templates/page_create_employee.xml',
        'templates/custom_partner_informations_front_view.xml',
        # 'data/data.xml',

        'views/inherited_res_config_views.xml',
        'views/inherited_partner_view.xml',
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
