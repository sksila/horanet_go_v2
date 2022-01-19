# -*- coding: utf-8 -*-
import logging
from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Set workflow values to all partners."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    res_partner_model = env['res.partner']

    _logger.info('Post init hook execution')

    env.context = res_partner_model.with_context(creation_mode=True).env.context
    env.add_todo(res_partner_model._fields['address_workflow'], res_partner_model.search([]))
    env.add_todo(res_partner_model._fields['garant_workflow'], res_partner_model.search([]))

    res_partner_model.recompute()
