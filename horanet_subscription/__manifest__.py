{
    # Module name in English
    'name': "Horanet Subscription",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.5.4',
    # Short description (with keywords)
    'summary': "POC contrats",
    'description': 'no_warning',
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Horanet/Subscription',
    #
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'web',
        'product',
        'sale',
        'decimal_precision',
        'account',
        # --- External --- #

        # --- Horanet --- #
        'partner_contact_identification',  # tag and assignation
        'horanet_web',  # sheet wider
        'horanet_go',
        'better_address',
        'partner_contact_citizen',  # view partner

    ],
    # always loaded
    'qweb': [],
    # list of XML files with data that will load to DB at moment when you install module
    'init_xml': [],
    # list of XML files with data that will load to DB at moment when you install or update module.
    'update_xml': [],
    # List of data files which must always be installed or updated with the module.
    'data': [
        'data/sequences.xml',
        'data/horanet_actions.xml',
        'data/ir_cron.xml',
        'data/ir_module_category.xml',
        'data/settings.xml',
        'data/decimal_precision.xml',
        'data/sale_settings.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',

        'wizards/wizard_activity_rule_sandbox_view.xml',
        'wizards/wizard_operation_recompute.xml',
        'wizards/wizard_activity_diagram_view.xml',
        'wizards/create_contract.xml',
        'wizards/wizard_subscription_update_date_view.xml',
        'wizards/wizard_package_update_date_view.xml',

        'views/horanet_prestation_view.xml',
        'views/horanet_service_view.xml',
        'views/horanet_activity_view.xml',
        'views/activity_sector_view.xml',
        'views/exploitation_engine/activity_rule_version_view.xml',
        'views/exploitation_engine/activity_rule_view.xml',
        'views/exploitation_engine/exploitation_engine_result_view.xml',

        'views/horanet_subscription_template_view.xml',
        'views/horanet_subscription_view.xml',
        'views/horanet_subscription_line_view.xml',
        'views/horanet_package_view.xml',
        'views/horanet_package_line_view.xml',
        'views/horanet_package_line_detail_view.xml',
        'views/horanet_infrastructure_view.xml',
        'views/horanet_subscription_cycle_view.xml',

        'views/exploitation_engine/device_query_view.xml',
        'views/exploitation_engine/device_response_view.xml',
        'views/exploitation_engine/horanet_operation_view.xml',
        'views/exploitation_engine/horanet_usage_view.xml',

        'views/horanet_device_view.xml',
        'views/device_check_point_view.xml',
        'views/horanet_action_view.xml',

        'views/inherited_sale_view.xml',
        'views/subscription_config_settings_view.xml',
        'views/inherited_product_view.xml',
        'views/inherited_partner_view.xml',
        'views/inherited_account_invoice_view.xml',
        'views/inherited_assignation_view.xml',

        'views/menu.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
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
