{
    # Module name in English
    'name': "Partner Documents Recipients",
    # Version, "odoo.min.yy.m.d"
    'version': '11.0.17.2.16',
    # Short description (with keywords)
    'summary': 'Gérez les bénéficiaires de vos documents',
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    'description': 'no warning',
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Knowledge',
    #
    'external_dependencies': {

    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        # --- Horanet --- #
        'partner_documents',
        'partner_contact_legal_relation',
        'partner_type_foyer',
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
        'templates/inherited_add_document_templates.xml',
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
