# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Delete old sequence environment_partner_internal_reference.

    And update new sequence horanet_partner_internal_reference
    """
    logger.info('Migration started: migrating partner internal reference sequence.')
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        old_sequence = env.ref('environment_waste_collect.seq_partner_internal_reference',
                               raise_if_not_found=False,
                               )
        new_sequence = env.ref('horanet_go.sequence_partner_internal_reference',
                               raise_if_not_found=False,
                               )

        if old_sequence:
            if new_sequence:
                new_sequence.write({
                    'prefix': old_sequence.prefix,
                    'suffix': old_sequence.suffix,
                    'use_date_range': old_sequence.use_date_range,
                    'padding': old_sequence.padding,
                    'number_increment': old_sequence.number_increment,
                    'number_next_actual': old_sequence.number_next_actual,
                })
                old_sequence_code = old_sequence.code
                # Drop old sequence : environment.partner.internal.reference from "ir.sequence" cause he's not used
                cr.execute("DELETE from ir_sequence where code = '{old_code}'".format(old_code=old_sequence_code))

            else:
                logger.info('The new sequence :horanet.partner.internal.reference is not found.')
        else:
            logger.info('The old sequence :environment.partner.internal.reference is not found.')

    logger.info('Migration ended: migrating partner internal reference sequence.')
