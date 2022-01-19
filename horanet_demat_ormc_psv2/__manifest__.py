# -*- coding: utf-8 -*-
{
    'name': "Horanet Export ORMC PSV2",
    'sequence': 2,
    # Short description (with keywords)
    'summary': "Export ORMC PSV2",
    # Description with metadata (in french)
    'description': "Dématérialisation PSV2",
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    'category': 'Dematerialisation',
    'version': '10.0.18.8.7',

    # any module necessary for this one to work correctly
    'depends': [
        # --- Odoo --- #
        'base',
        'account',
        'sale',
        'account_accountant',
        'l10n_fr',
        # --- External --- #
        # --- Horanet --- #
        'horanet_go',
        'account_mass_invoicing',
        'horanet_website_account',  # to add CatTiers and NatJur in partner front template
    ],
    # always loaded
    'data': [
        'data/ir_sequence_data.xml',
        'data/data_partner.xml',
        'data/data_application.xml',
        # Le référentiel
        'data/base/data_ref_value.xml',
        'data/base/data_ref_value_constraint.xml',
        'data/base/data_ref.xml',
        # Général
        'data/base/data_domain.xml',
        'data/base/data_input_object.xml',
        'data/data_domain.xml',
        'data/data_input_object.xml',
        # Les attributs
        'data/base/data_bloc_attrs.xml',
        'data/general/data_bloc_attrs.xml',
        'data/facture/data_bloc_attrs.xml',
        'data/recette_aller/data_bloc_attrs.xml',
        'data/PES_PJ/data_bloc_attrs.xml',
        # Les blocs
        'data/base/data_bloc.xml',
        'data/facture/data_bloc.xml',
        'data/recette_aller/data_bloc.xml',
        'data/PES_PJ/data_bloc.xml',
        'data/general/data_bloc.xml',

        'data/base/data_file_type.xml',
        'data/data_file.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',

        'templates/inherit_partner_informations_templates.xml',

        'wizards/pes_export_wizard_view.xml',
        'wizards/pes_import_wizard_view.xml',

        'views/pes_referential_view.xml',
        'views/pes_referential_value_view.xml',
        'views/pes_referential_value_constraint_view.xml',
        'views/pes_domain_view.xml',
        'views/pes_file_type_view.xml',
        'views/pes_input_object_view.xml',
        'views/pes_bloc_attrs_view.xml',
        'views/pes_bloc_view.xml',
        'views/pes_file_view.xml',
        'views/pes_declaration_file_view.xml',
        'views/pes_declaration_view.xml',
        'views/inherited_company_view.xml',
        'views/inherited_product_template_view.xml',
        'views/inherited_horanet_budget_code_view.xml',
        'views/inherited_partner_view.xml',
        'views/inherited_horanet_role_view.xml',
        'views/pes_application_view.xml',
        'views/pes_message_view.xml',
        'views/inherited_collectivity_config_setting_view.xml',

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
    'post_init_hook': 'post_init_hook',
}
