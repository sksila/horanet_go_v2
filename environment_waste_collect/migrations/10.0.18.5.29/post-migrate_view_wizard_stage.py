# coding: utf-8

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Attribute the correct view for the different stage of the partner setup wizard."""
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # étapes du wizard
        wizard_stage_subscription_template_choice = env.ref(
            'environment_waste_collect.wizard_stage_subscription_template_choice',
            raise_if_not_found=False,
        )
        wizard_stage_support_attribution = env.ref(
            'environment_waste_collect.wizard_stage_support_attribution',
            raise_if_not_found=False,
        )
        wizard_stage_fixed_part_choice = env.ref(
            'environment_waste_collect.wizard_stage_fixed_part_choice',
            raise_if_not_found=False,
        )
        wizard_stage_summary = env.ref(
            'environment_waste_collect.wizard_stage_summary',
            raise_if_not_found=False,
        )

        # Vue des étapes
        view_partner_setup_wizard_stage_template_choice = env.ref(
            'environment_waste_collect.view_partner_setup_wizard_stage_template_choice',
            raise_if_not_found=False,
        )
        view_partner_setup_wizard_stage_support_attribution = env.ref(
            'environment_waste_collect.view_partner_setup_wizard_stage_support_attribution',
            raise_if_not_found=False,
        )
        view_partner_setup_wizard_stage_fixed_part_choice = env.ref(
            'environment_waste_collect.view_partner_setup_wizard_stage_fixed_part_choice',
            raise_if_not_found=False,
        )
        view_partner_setup_wizard_summary = env.ref(
            'environment_waste_collect.view_partner_setup_wizard_summary',
            raise_if_not_found=False,
        )

        if wizard_stage_subscription_template_choice and view_partner_setup_wizard_stage_template_choice and\
                not wizard_stage_subscription_template_choice.view_id:
            wizard_stage_subscription_template_choice.write({
                'view_id': view_partner_setup_wizard_stage_template_choice.id})

        if wizard_stage_support_attribution and view_partner_setup_wizard_stage_support_attribution and \
                not wizard_stage_support_attribution.view_id:
            wizard_stage_support_attribution.write({
                'view_id': view_partner_setup_wizard_stage_support_attribution.id})

        if wizard_stage_fixed_part_choice and view_partner_setup_wizard_stage_fixed_part_choice and \
                not wizard_stage_fixed_part_choice.view_id:
            wizard_stage_fixed_part_choice.write({
                'view_id': view_partner_setup_wizard_stage_fixed_part_choice.id,
            })

        if wizard_stage_summary and view_partner_setup_wizard_summary and \
                not wizard_stage_summary.view_id:
            wizard_stage_summary.write({
                'view_id': view_partner_setup_wizard_summary.id,
            })
