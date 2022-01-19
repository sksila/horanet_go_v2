# -*- coding: utf-8 -*-

__name__ = 'Update document type validity period from months to days'

import logging
from odoo import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Update document type validity period from months to days."""
    logger.info("Migration started: migrating document type validity period.")
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        documents_types = env['ir.attachment.type'].search([('validity_period', '!=', False)])
        for doc in documents_types:
            doc.validity_period = doc.validity_period * 30

    logger.info("Migration ended: migrating document type validity period.")
