# -*- coding: utf-8 -*-

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger("Delete sulo_environment_config_settings")


def migrate(cr, version):
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

    old_setting_view = env.ref('environment_waste_collect_cardmaker_export.sulo_environment_config_settings',
                               raise_if_not_found=False,
                               )

    if old_setting_view:
        old_setting_view.unlink()
