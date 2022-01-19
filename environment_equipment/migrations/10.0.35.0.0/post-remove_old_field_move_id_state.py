# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Delete old value of move_id_state because we change the name into is_move_id_active."""
    if not version:
        return

    cr.execute("DELETE FROM ir_model_fields "
               "WHERE name = 'move_id_state' AND model = 'partner.move.equipment.rel';")

    logger.info('Migration ended: delete move_id_state of ir_model_fields.')
