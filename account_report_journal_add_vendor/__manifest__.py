# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "Add vendor in salle/purchase journal",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.17.6.12',
    # Short description (with keywords)
    'summary': "",
    # Description with metadata (in french)
    'description': "Add vendor in account salle/purchase journal",
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
        'account'
        # --- External --- #

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
        'views/inherited_account_report_print_journal_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    'application': False,
    'auto_install': False,
    # permet d'installer automatiquement le module si toutes ses dépendances sont installés
    # -default value set is False
    # -If false, the dependent modules are not installed if not installed prior to the dependent module.
    # -If True, all corresponding dependent modules are installed at the time of installing this module.
    'installable': False
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
