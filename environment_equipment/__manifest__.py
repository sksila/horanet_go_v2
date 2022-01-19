{
    # Module name in English
    'name': "Environment Equipment",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.35.0.0',
    # Short description (with keywords)
    'summary': "Gestion des bacs",
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
        # --- Horanet --- #
        'environment_waste_collect',
        'environment_production_point',
        'environment_applications',
        'maintenance',
        'website_portal',
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
        'data/data.xml',

        'views/inherited_maintenance_equipment_view.xml',
        'views/inherited_maintenance_request_view.xml',
        'views/inherited_environment_applications_view.xml',
        'views/inherited_maintenance_equipment_category_view.xml',
        'views/maintenance_intervention_type_view.xml',
        'views/inherited_horanet_operation_view.xml',
        'views/inherited_partner_view.xml',
        'views/equipment_pickup_import.xml',
        'views/partner_move_equipment_rel_view.xml',
        'views/equipment_status.xml',
        'views/inherited_activity_view.xml',
        'views/inherited_report_invoice_sepa.xml',
        'views/menu.xml',

        'templates/inherited_website_portal_templates.xml',
        'templates/my_pickups_template.xml',

        'wizards/inherited_partner_setup_wizard_view.xml',
        'wizards/partner_setup_wizard_stages.xml',
        'wizards/inherited_partner_close_contract_wizard_view.xml',

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
    'installable': False,
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
