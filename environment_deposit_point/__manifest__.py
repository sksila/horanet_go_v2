# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "Environment Deposit Point",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.17.11.09',
    # Short description (with keywords)
    'summary': "Gestion des points d'apport volontaire",
    # Description with metadata (in french)
    'description': 'no_warning',
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Horanet/Environment',
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
        'horanet_environment',
        'horanet_subscription',
        'environment_waste_collect',
        'environment_equipment',
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
        'security/ir.model.access.csv',

        'data/sequences.xml',
        'data/product_uoms.xml',
        'data/actions.xml',
        'data/activities.xml',
        'data/activity_sectors.xml',

        'views/deposit_point_view.xml',
        'views/deposit_area_view.xml',
        'views/inherit_operation_view.xml',
        'views/deposit_import_data_view.xml',
        'views/inherited_partner_view.xml',
        'views/inherited_collectivity_config_settings_view.xml',
        'views/inherited_activity_view.xml',
        'views/inherited_report_invoice_sepa.xml',

        'templates/inherited_website_portal_templates.xml',
        'templates/my_deposits_template.xml',

        'wizards/inherited_partner_setup_wizard_view.xml',

        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'data/demo.xml'
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
