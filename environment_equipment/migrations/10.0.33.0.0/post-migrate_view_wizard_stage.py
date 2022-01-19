# coding: utf-8

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Attribute the correct view for the different stage of the partner setup wizard."""
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # étapes du wizard

        wizard_stage_equipment_attribution = env.ref(
            'environment_equipment.wizard_stage_equipment_attribution',
            raise_if_not_found=False,
        )

        # Vue des étapes
        view_partner_setup_wizard_stage_equipment_attribution = env.ref(
            'environment_equipment.view_partner_setup_wizard_stage_equipment_attribution',
            raise_if_not_found=False,
        )

        if wizard_stage_equipment_attribution and view_partner_setup_wizard_stage_equipment_attribution \
                and not wizard_stage_equipment_attribution.view_id:

            wizard_stage_equipment_attribution.write({
                'view_id': view_partner_setup_wizard_stage_equipment_attribution.id
            })
