# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    u"""
    Suppression de l'étape Accounting data du wizard.

    Sinon, mise à jour impossible.
    """
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        xml_id = 'account_mass_invoicing.wizard_stage_accounting_data'
        res_id = env['ir.model.data'].xmlid_to_res_id(xml_id)

        if res_id:
            cr.execute("DELETE from partner_setup_wizard_stage where id = {res_id}".format(res_id=res_id))
            cr.execute("DELETE from ir_model_data where module || '.' || name = '{xml_id}'".format(xml_id=xml_id))

        view_to_delete = env.ref('account_mass_invoicing.inherited_view_partner_setup_wizard_summary_accounting_data',
                                 raise_if_not_found=False)
        if view_to_delete:
            view_to_delete.unlink()

    _logger.info("End suppression accounting data stage")
