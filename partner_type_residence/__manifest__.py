# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "Partner type Residence",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.17.2.9',
    # Short description (with keywords)
    'summary': "Ajoute un type 'Residence' pour les partner",
    # Description with metadata (in french)
    'description': "no_warning",
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Human Resources',
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #

        # --- External --- #
        'base_partner_merge',
        'partner_relations',
        'partner_firstname',
        'partner_contact_personal_information_page',

        # --- Horanet --- #
        'horanet_location',
        # 'web_fields_masks', liée à horanet_web
        'horanet_web',  # pour agrandir les vues partner
        # 'horanet_go', liée à horanet_location/horanet_web

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
        'views/inherited_partner_view.xml',
        'views/inherited_partner_title_view.xml',
        'views/partner_citizen_view.xml',
        'views/partner_residence_view.xml',
        'views/partner_foyer_view.xml',
        'views/relation_foyer_view.xml',
        'views/relation_residence_view.xml',
        'wizards/wizard_import_data_partner_view.xml',
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
    'installable': False
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
