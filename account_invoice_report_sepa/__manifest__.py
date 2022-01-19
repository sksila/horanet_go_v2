# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "Invoice Report SEPA",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.06.20',
    # Short description (with keywords)
    'summary': "Factures SEPA",
    # Description with metadata (in french)
    'description': 'no_warning',
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Horanet/Invoicing',
    #
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'partner_documents',
        'account',
        # --- External --- #
        'account_banking_sepa_direct_debit',
        # --- Horanet --- #
        'horanet_demat_ormc_psv2',
        'account_mass_invoicing',
        'horanet_subscription',
        'partner_contact_second_names',  # lastname2, firstname2
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
        'data/report_paperformat.xml',
        'data/document_types.xml',
        'views/style.xml',
        'views/report_invoice_sepa.xml',
        'views/report_sepa_dynamic_elements_view.xml',
        'views/inherited_account_settings_view.xml',
        'views/external_layout_sepa.xml',
        'views/inherited_horanet_role_view.xml',
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
    'installable': False,
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
