# coding: utf8

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Remove external ids and views after view id renaming."""
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        old_views_external_ids = [
            'horanet_auth_signup.inherited_auth_signup_config_view',
            'horanet_auth_signup.inherited_base_setup']

        for external_id in old_views_external_ids:
            rec = env.ref(external_id, raise_if_not_found=False)
            if rec:
                # emulate an ondelete cascade, using view model unlink overwrite
                rec.with_context(_force_unlink=True).unlink()
