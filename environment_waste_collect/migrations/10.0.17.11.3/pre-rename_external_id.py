# coding: utf-8

import logging
from odoo import api, SUPERUSER_ID

__name__ = 'Migration : Change external id of activity form view'
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Clear old external ID and it's linked record."""
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        old_view = env.ref('environment_waste_collect.activity_form_view', raise_if_not_found=False)
        if old_view:
            old_view.unlink()
        _logger.debug('Renamed External id: activity_form_view -> smart_eco_activity_form_view')
