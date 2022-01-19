{
    # Module name in English
    'name': "Website Application",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.17.11.27',
    # Short description (with keywords)
    'summary': "Gestion des téléservices",
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
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'portal',
        'website',
        # --- External --- #
        # --- Horanet --- #
        'horanet_go',
        'horanet_subscription',
        'horanet_auth_signup',
        'partner_documents',
        'better_address',
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

        'data/application_sequence.xml',
        'data/application_functionalities.xml',
        'data/document_types.xml',
        'data/sequences.xml',
        'data/application_informations.xml',

        'views/website_application_view.xml',
        'views/website_application_template_view.xml',
        'views/application_information_view.xml',
        'views/inherited_partner_view.xml',
        'views/email_template.xml',
        'views/menu.xml',

        'templates/website_applications_template.xml',
        'templates/website_application_create_template.xml',
        'templates/website_application_template_create_template.xml',
        'templates/website_application_see_template.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
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
}
