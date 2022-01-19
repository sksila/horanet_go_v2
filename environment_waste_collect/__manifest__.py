{
    # Module name in English
    'name': "Environment Waste Collect",
    # Version, "odoo.min.yy.m.d"
    'version': '11.0.18.12.21',
    # Short description (with keywords)
    'summary': "Gestion de collecte des déchets",
    # Description with metadata (in french)
    'description': 'no_warning',
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

        # --- External --- #
        'partner_identification',
        'email_template_qweb',  # Permet d'utiliser le qweb dans les mail
        'report_xlsx',

        # --- Horanet --- #
        'horanet_environment',
        'horanet_web',  # better_gauge # route
        'partner_type_foyer',
        'partner_contact_legal_relation',
        'horanet_subscription',
        'better_address',
        'horanet_go',
        'partner_contact_citizen',
        'partner_contact_identification',  # tag and assignation
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
        'data/res_config.xml',
        'data/horanet_actions.xml',
        'data/product_uoms.xml',
        'data/activities.xml',
        'data/sequences.xml',
        'data/mail_templates.xml',
        'data/decimal_precision.xml',
        'data/partner_categories.xml',
        'data/partner_category_environment.xml',
        'data/identification_categories.xml',
        'data/file_attachment.xml',
        'data/ir_cron.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',

        'wizards/pickup_request_report_wizard_view.xml',
        'wizards/environment_partner_report_wizard_view.xml',
        'wizards/manage_wastesite_fmi_wizard.xml',
        'wizards/partner_setup_wizard_view.xml',
        'wizards/partner_setup_wizard_stages.xml',
        'wizards/partner_close_contract_wizard_view.xml',
        'wizards/environment_operation_report_wizard_view.xml',

        'report/pickup_request_report.xml',
        'report/environment_partner_report.xml',
        'report/environment_operation_report.xml',
        'report/environment_operation_xls_report.xml',
        'report/pickup_request_xls_report.xml',

        'views/pickup_contract_view.xml',
        'views/pickup_request_view.xml',
        'views/container_type_view.xml',
        'views/container_view.xml',
        'views/emplacement_view.xml',
        'views/inherited_config_settings.xml',
        'views/ecopad_session_view.xml',
        'views/ecopad_transaction_view.xml',
        'views/inherited_report_invoice_sepa.xml',

        'views/inherited_device_check_point_view.xml',
        'views/waste_site.xml',

        'views/inherited_horanet_subscription_view.xml',
        'views/inherited_operation_view.xml',
        'views/inherited_partner_view.xml',
        'views/partner_category_view.xml',
        'views/contract_cycle_view.xml',
        'views/activity_view.xml',
        'views/service_view.xml',
        'views/prestation_view.xml',
        'views/contract_template_view.xml',
        'views/activity_sector_view.xml',
        'views/activity_rule_view.xml',
        'views/rule_editor_view.xml',
        'views/inherited_horanet_device_view.xml',
        'views/inherited_category_partner_view.xml',
        'views/inherited_account_invoice_view.xml',
        'views/custom_env_partner_form_view.xml',

        'views/inherited_assignation_view.xml',

        'templates/inherited_website_portal_templates.xml',
        'templates/my_deposits_template.xml',
        'templates/my_access_template.xml',

        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
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
