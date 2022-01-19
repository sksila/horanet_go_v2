# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "TCO Inscription transports scolaires",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.06.22',
    # Short description (with keywords)
    'summary': "Gestion des Inscription au transport scolaire",
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
        'account',
        'sale',
        'product',
        'base_geolocalize',
        # --- External --- #
        #  échéancier (OCA account-invoicing)
        'account_payment_term_extension',
        # --- Horanet --- #
        'horanet_website',
        'horanet_auth_signup',
        'horanet_school',
        'tco_transport',
        'tco_validation',
        'partner_contact_identification',
        'partner_type_foyer',
        'partner_documents_recipients',
        'website_application',
        'horanet_transport',
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
        'security/ir.model.access.csv',
        'security/record_rules.xml',

        'data/data.xml',
        'data/document_type.xml',
        'data/inscription_sequence.xml',
        'data/mail_templates.xml',
        'data/application_functionalities.xml',
        'data/application_informations.xml',
        'data/application_templates.xml',
        'data/report_paperformat.xml',

        'wizards/wizard_refuse_inscription_view.xml',
        'wizards/wizard_create_so_invoice_view.xml',

        'views/tco_inscription_view.xml',
        'views/tco_inscription_period_view.xml',
        'views/inherited_pricelist_view.xml',
        'views/inherited_product_view.xml',
        'views/inherited_product_template_view.xml',
        'views/inherited_payment_term_view.xml',
        'views/inherited_account_invoice_view.xml',
        'views/inherited_sale_order_view.xml',
        'views/inherited_partner_view.xml',
        'views/inherited_school_establishment.xml',
        'views/inherited_tco_transport_line.xml',
        'views/inherited_tco_transport_station.xml',
        'views/inherited_horanet_transport_config_view.xml',

        'templates/website_assets_frontend.xml',
        'templates/inscription_templates.xml',
        'templates/inherited_website_application_template.xml',
        'templates/inherited_page_cru_foyer_member.xml',

        'reports/tco_inscription_report.xml',
        'reports/tco_inscription_global_report.xml',
        'reports/tco_inscription_report_affectation.xml',

        'views/menu.xml',

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
