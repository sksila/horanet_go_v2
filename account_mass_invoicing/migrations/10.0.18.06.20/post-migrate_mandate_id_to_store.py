# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Update invoice.mandate_id values in old records .

    after the modification of store (store=True) attribute of field mandate_id .
    """
    if not version:
        return
    with api.Environment.manage():

        env = api.Environment(cr, SUPERUSER_ID, {})

        invoice_ids = env['account.invoice'].search([('mandate_id', '=', False)])
        logger.info("{} mandates to compute".format(len(invoice_ids)))
        for index, invoice in enumerate(invoice_ids):
            invoice._compute_mandate_id()
            logger.info("{}/{} mandates computed".format(index + 1, len(invoice_ids)))
