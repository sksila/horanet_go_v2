{
    # Module name in English
    'name': "Personal information for contacts",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.17.2.8',
    # Short description (with keywords)
    'summary': "Add a page to contacts form to put personal information like birthdate, age, gender ...",
    'description': 'no warning',
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Customer Relationship Management',
    #
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'web',

        # --- External --- #
        'partner_contact_personal_information_page',
        # --- Horanet --- #
        'horanet_go',  # For configuration page and groups
        'horanet_auth_signup',  # For altering citizen template

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
        'views/inherited_partner_view.xml',
        'views/inherited_partner_title_view.xml',
        'views/inherited_collectivity_config_settings_view.xml',

        'data/inherit_auth_signup_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
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
