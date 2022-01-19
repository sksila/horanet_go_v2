{
    # Module name in English
    'name': "Horanet Transport",
    # Version, "odoo.min.yy.m.d"
    'version': '11.0.18.12.19',
    # Short description (with keywords)
    'summary': "Contient les modèles de base d'une gestion du transport",
    # Description with metadata (in french)
    'description': 'no_warning',
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    'category': 'Horanet/School transport',
    #
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        # --- External --- #
        # --- Horanet --- #
        'horanet_subscription',  # for application_type
        'website_application',
        'partner_contact_citizen',
    ],
    # always loaded
    'css': [],
    'qweb': [],
    # list of XML files with data that will load to DB at moment when you install module
    'init_xml': [],
    # list of XML files with data that will load to DB at moment when you install or update module.
    'update_xml': [],
    # List of data files which must always be installed or updated with the module.
    'data': [
        'data/ir_module_category.xml',
        'security/groups.xml',

        'views/partner_transport_view.xml',
        'views/custom_partner_transport_form_view.xml',

        'views/inherited_website_application_view.xml',
        'views/inherited_website_application_template_view.xml',
        'views/config_settings.xml',
        'views/menu.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
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
}
