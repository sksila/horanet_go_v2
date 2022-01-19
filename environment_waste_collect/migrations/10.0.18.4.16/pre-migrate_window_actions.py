# coding: utf-8

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Delete old windows action du recreate them with update architecture."""
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        old_access_action = env.ref('environment_waste_collect.access_action', raise_if_not_found=False)
        if old_access_action:
            if old_access_action.view_ids:
                old_access_action.view_ids.unlink()
            old_access_action.unlink()

        old_deposit_action = env.ref('environment_waste_collect.deposit_action', raise_if_not_found=False)
        if old_deposit_action:
            if old_deposit_action.view_ids:
                old_deposit_action.view_ids.unlink()
            old_deposit_action.unlink()

        records_to_delete = [
            'environment_waste_collect.operation_search_view',
            'environment_waste_collect.operation_tree_view',
            'environment_waste_collect.operation_deposit_form_view',
            'environment_waste_collect.operation_form_view']

        for record_to_delete in records_to_delete:
            old_record = env.ref(record_to_delete, raise_if_not_found=False)
            if old_record:
                old_record.unlink()
