# -*- coding: utf-8 -*-

import logging

from odoo import SUPERUSER_ID, api

try:
    from odoo.addons.horanet_go.tools import migrations
except ImportError:
    from horanet_go.tools import migrations

logger = logging.getLogger('horanet_demat_ormc_psv2')


def post_init_hook(cr, registry):
    u"""
    Post-install script.

    Migration des données des anciens modules puis suppression de la liste des modules.
    Migration des pays pour ajout le code pays numérique sur 3 caractères.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    is_hn_demat_data_nsbase_module_installed = env['ir.module.module'].search([
        ('name', '=', 'hn_demat_data_nsbase'),
        ('state', '=', 'installed'),
    ])

    is_hn_demat_psv2_module_installed = env['ir.module.module'].search([
        ('name', '=', 'hn_demat_psv2'),
        ('state', '=', 'installed'),
    ])

    is_hn_demat_const_module_installed = env['ir.module.module'].search([
        ('name', '=', 'hn_demat_const'),
        ('state', '=', 'installed'),
    ])

    if is_hn_demat_data_nsbase_module_installed:
        # Si le champ cat_tiers existe, alors migration cat_tiers
        if migrations.get_field_exists(env.cr, 'res_partner', 'cat_tiers'):
            migrate_cat_tiers(env)

        # Si le champ nat_jur existe, alors migration nat_jur
        if migrations.get_field_exists(env.cr, 'res_partner', 'nat_jur'):
            migrate_nat_jur(env)

    # Si module hn_demat_psv2 est installé, alors migration declarations et declaration files
    if is_hn_demat_psv2_module_installed:
        migrate_declarations(env)

    # Si module hn_demat_const est installé, alors migration données société et budget
    if is_hn_demat_const_module_installed:
        migrate_company_and_budget(env)

    migrate_countries(env)

    uninstall_hn_modules(env)


def migrate_cat_tiers(env):
    logger.info("Starting Migration of cat_tiers field")
    env.cr.execute(
        """UPDATE res_partner
           SET cat_tiers_id = (
               SELECT id
               FROM pes_referential_value
               WHERE ref_id = {ref_id}
               AND value = (
                   SELECT value
                   FROM dm_pes_ref_value
                   WHERE id = cat_tiers
               )
           )
           WHERE cat_tiers IS NOT NULL""".format(
            ref_id=env.ref('horanet_demat_ormc_psv2.pes_ref_cat_tiers').id
        )
    )


def migrate_nat_jur(env):
    logger.info("Starting Migration of nat_jur field")
    env.cr.execute(
        """UPDATE res_partner
           SET nat_jur_id = (
               SELECT id
               FROM pes_referential_value
               WHERE ref_id = {ref_id}
               AND value = (
                   SELECT value
                   FROM dm_pes_ref_value
                   WHERE id = nat_jur
               )
           )
           WHERE nat_jur IS NOT NULL""".format(
            ref_id=env.ref('horanet_demat_ormc_psv2.pes_ref_nat_jur').id
        )
    )


def migrate_declarations(env):
    logger.info('Starting Migration of declarations')
    old_declaration_model = env['dm.pes.declaration']
    old_declaration_file_model = env['dm.pes.declaration.file']
    new_declaration_model = env['pes.declaration']
    new_declaration_file_model = env['pes.declaration.file']

    declarations_to_migrate = old_declaration_model.search([('role_id', '!=', False)])

    for old_declaration in declarations_to_migrate:
        new_declaration = new_declaration_model.create({
            'role_id': old_declaration.role_id.id,
            'state': old_declaration.state,
            'date_declaration': old_declaration.date_declaration,
            'name': old_declaration.name,
            'pes_domain_id': env.ref('horanet_demat_ormc_psv2.pes_domain_1').id,
        })

        declaration_files_to_migrate = old_declaration_file_model.search([('declaration_id', '=', old_declaration.id)])

        for old_declaration_file in declaration_files_to_migrate:
            new_declaration_file_model.create({
                'name': old_declaration_file.filename,
                'pes_declaration_id': new_declaration.id,
                'filename': old_declaration_file.filename,
                'data': old_declaration_file.data
            })


def migrate_company_and_budget(env):
    logger.info('Starting Migration of company and budget')
    env.cr.execute(
        "UPDATE res_company SET ormc_id_post = id_post, ormc_cod_col = cod_col"
    )
    env.cr.execute(
        "UPDATE horanet_budget_code SET ormc_cod_bud = cod_bud, ormc_libelle_cod_bud = libelle_cod_bud"
    )


def migrate_countries(env):
    logger.info('Starting Migration of countries')
    countries = env['res.country'].search([])
    # Data CodPays
    countries.filtered(lambda r: r.code == 'BE').write({'ormc_cod_pays': '056'})
    countries.filtered(lambda r: r.code == 'CA').write({'ormc_cod_pays': '124'})
    countries.filtered(lambda r: r.code == 'CH').write({'ormc_cod_pays': '756'})
    countries.filtered(lambda r: r.code == 'DE').write({'ormc_cod_pays': '276'})
    countries.filtered(lambda r: r.code == 'ES').write({'ormc_cod_pays': '724'})
    countries.filtered(lambda r: r.code == 'FI').write({'ormc_cod_pays': '246'})
    countries.filtered(lambda r: r.code == 'FR').write({'ormc_cod_pays': '100'})
    countries.filtered(lambda r: r.code == 'GB').write({'ormc_cod_pays': '826'})
    countries.filtered(lambda r: r.code == 'IE').write({'ormc_cod_pays': '372'})
    countries.filtered(lambda r: r.code == 'NL').write({'ormc_cod_pays': '528'})
    countries.filtered(lambda r: r.code == 'PE').write({'ormc_cod_pays': '604'})
    countries.filtered(lambda r: r.code == 'US').write({'ormc_cod_pays': '840'})


def uninstall_hn_modules(env):
    u"""Suppression de la référence des modules hn de la liste des modules."""
    logger.info("Starting Unsinstallation of HN modules")
    modules_to_uninstall = [
        'hn_demat_psv2',
        'hn_message_center',
        'hn_demat_data_nsfacture',
        # 'hn_demat_data_nsbase',
        # 'hn_demat_const',
    ]

    for module_name in modules_to_uninstall:
        module = env['ir.module.module'].search([
            ('name', '=', module_name),
        ])
        if module:
            module.write({'state': 'to remove'})
            module.module_uninstall()
            module.unlink()
