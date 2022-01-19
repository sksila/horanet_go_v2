# -*- coding: utf-8 -*-
{
    # Module name in English
    'name': "Horanet eCommerce",
    # Version, "odoo.min.yy.m.d"
    'version': '10.0.18.12.25',
    # Short description (with keywords)
    'summary': "Adapte le portail de vente pour les collectivités",
    # Description with metadata (in french)
    'description': "Adapte le portail de vente pour les collectivités",
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    # distribution license for the module (defaults: AGPL-3)
    'license': "AGPL-3",
    'contributors': [
        'Maximilien TANTIN',
    ],
    # Categories can be used to filter modules in modules listing. For the full list :
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    'category': 'Collectivity',
    #
    'external_dependencies': {
        'python': []
    },
    # any module necessary for this one to work correctly. Either because this module uses features
    # they create or because it alters resources they define.
    'depends': [
        # --- Odoo --- #
        'sale_management',
        'web',
        'website_sale',

        # --- External --- #

        # --- Horanet --- #
        'horanet_go',
        'horanet_website_account',
        'better_address',
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
        'data/res_config.xml',

        'report/inherited_sale_report.xml',

        'templates/assets_frontend.xml',
        'templates/inherited_address_checkout.xml',
        'templates/inherited_accept_terms.xml',
        'templates/inherited_confirmation.xml',
        'templates/inherited_product_public_category.xml',
        'templates/inherited_total.xml',
        'templates/inherited_cart.xml',
        'templates/inherited_product.xml',

        'views/inherited_product_public_category_views.xml',
        'views/inherited_res_config_view.xml',
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
    'installable': True,
    # -True, module can be installed.
    # -False, module is listed in application, but cannot install them.
}
