{
    # Module name in English
    'name': "Partner Documents",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.9.18',
    # Short description (with keywords)
    'summary': 'Gérez vos documents !',
    'description': 'no warning',
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Knowledge',
    #
    'external_dependencies': {
        'python': [
            'magic',  # real package is python-magic
        ]
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'portal',
        'website',
        # --- Horanet --- #
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
        'views/inherited_document_view.xml',
        'views/document_type_view.xml',
        'views/menu.xml',

        'templates/add_document_form_template.xml',
        'templates/documents_templates.xml',
        'templates/document_templates.xml',
        'templates/add_document_templates.xml',
        'templates/inherited_website_portal_template.xml',

        'data/document_types.xml',
        'data/groups.xml',
        'data/ir_cron.xml',

        'security/rules.xml',
        'security/ir.model.access.csv',
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
