# -*- coding: utf-8 -*-
{
    'name': "Environment Production Point",
    'version': '10.0.18.11.20',
    'summary': "Gestion des points de production",
    'description': 'no_warning',
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    'license': "AGPL-3",
    'category': 'Human Resources',
    'external_dependencies': {
        'python': []
    },
    'depends': [
        # --- Odoo --- #
        'account',
        # --- External --- #

        # --- Horanet --- #
        'horanet_environment',
        'environment_waste_collect',
        'partner_contact_identification',  # assignation
    ],
    'css': [],
    'qweb': [],
    'init_xml': [],
    'update_xml': [],
    'data': [
        'security/ir.model.access.csv',

        'views/production_point_view.xml',
        'views/partner_move_view.xml',

        'views/inherited_partner_view.xml',
        'views/inherited_config_settings_view.xml',
        'views/inherited_assignation_view.xml',
        'views/inherited_report_invoice_sepa.xml',

        'views/menu.xml',

        'wizards/inherited_partner_setup_wizard_view.xml',
        'wizards/partner_setup_wizard_stages.xml',
        'wizards/inherited_partner_close_contract_wizard_view.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': False,
}
