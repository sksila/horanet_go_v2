# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "Account Mass Invoicing",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.09.14',
    # Short description (with keywords)
    'summary': "Contient les modèles de base d'une gestion des rôles / lots / campagnes de facturation",
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
        'account',
        'account_accountant',
        # --- External --- #
        'account_payment_term_extension',
        'account_banking_sepa_direct_debit',
        # --- Horanet --- #
        'horanet_subscription',
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
        'security/groups.xml',
        'security/ir.model.access.csv',

        'data/payment_methods.xml',

        'views/horanet_campaign_prestation_period_view.xml',
        'views/horanet_invoice_batch_view.xml',
        'views/horanet_invoice_batch_type_view.xml',
        'views/horanet_invoice_campaign_view.xml',
        'views/horanet_role_view.xml',
        'views/inherited_horanet_subscription.xml',
        'views/inherited_partner_view_buttons.xml',
        'views/inherited_account_payment_method.xml',
        'views/horanet_budget_code_view.xml',
        'views/accounting_date_range_view.xml',
        'views/inherited_account_invoice_view.xml',
        'views/inherited_account_config_settings_view.xml',

        'wizards/wizard_mass_invoicing_view.xml',
        # import ORDOTIP
        'wizards/import_ordotip_wizard.xml',
        'views/menu.xml',
        # report Role
        'views/report_role_mass_invoice.xml',
        'views/report_batch_mass_invoice.xml',
        'views/external_layout_role.xml',
        'views/external_layout_batch.xml',
        'report/report.xml',
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
