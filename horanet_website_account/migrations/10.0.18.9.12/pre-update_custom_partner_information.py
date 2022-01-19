# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Modify parameter noupdate of custom_partner_informations_front_view.

    As we changed the company_title in the partner_informations, the view custom_partner_informations_front_view must
    be change too.
    """
    logger.info("Pre Migration started: updating noupdate parameter of custom_partner_informations_front_view data.")
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

    rec_ir_model_data = env['ir.model.data'].search(
        [('module', '=', 'horanet_website_account'),
         ('name', '=', 'custom_partner_informations_front_view')])

    rec_ir_view = env.ref('horanet_website_account.custom_partner_informations_front_view', raise_if_not_found=False)

    if rec_ir_model_data and rec_ir_view:
        # on met le noupdate a false afin de recharger la vue
        rec_ir_model_data.write({'noupdate': False})

        # on supprime l'ancienne vue de la base
        rec_ir_view.unlink()

    logger.info("Pre Migration ended: custom_partner_informations_front_view data updated.")
