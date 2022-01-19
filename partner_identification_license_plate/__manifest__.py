# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "Partner identification License Plate",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.01.11',
    # Short description (with keywords)
    'summary': "Identification par plaque d'immatriculation",
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
        # --- External --- #
        # --- Horanet --- #
        'partner_contact_identification',
        'website_application',  # Pour les téléservices
        'environment_applications',  # Pour le type de document 'carte grise'
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
        'data/action_server.xml',
        'data/identifications.xml',
        'data/data_vehicle_type.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',

        'views/inherited_application_information_view.xml',
        'views/horanet_vehicle_type_view.xml',
        'views/horanet_vehicle_view.xml',
        'views/inherited_partner_view.xml',

        'templates/inherited_website_application_template_create_template.xml',

        'wizards/inherited_wizard_create_identification_view.xml',
        'wizards/wizard_create_vehicle_view.xml',

        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
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
