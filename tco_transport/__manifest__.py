# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "TCO Transport",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.05.04',
    # Short description (with keywords)
    'summary': "Contient les modèles de gestion des lignes de transport",
    'description': "no warning",
    # Description with metadata (in french)
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Transports',
    #
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'decimal_precision',

        # --- External --- #
        'auditlog',
        # --- Horanet --- #
        'horanet_web',
        'better_address',
        'partner_contact_identification',
        'horanet_transport',
        # 'horanet_go', liée à location
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
        'security/groups.xml',
        'security/ir.model.access.csv',

        'wizards/terminal_lb7_configure.xml',
        'views/transport_station_view.xml',
        'views/transport_station_type_view.xml',
        'views/transport_stop_view.xml',
        'views/transport_line_view.xml',
        'views/transport_service_view.xml',
        'views/transport_vehicle_category_view.xml',
        'views/transport_vehicle_brand_view.xml',
        'views/transport_vehicle_model_view.xml',
        'views/transport_vehicle_view.xml',
        'views/transport_vehicle_assignment_view.xml',
        'views/terminal_software_view.xml',
        'views/terminal_view.xml',
        'views/pointage_view.xml',
        'views/terminal_lb7_log_view.xml',
        'views/menu.xml',
        'views/inherited_horanet_transport_config_view.xml',

        'data/actions.xml',
        'data/config.xml',
        'data/decimal_precision.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/transport_demo.xml',
        'demo/terminal_demo.xml',
    ],
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
