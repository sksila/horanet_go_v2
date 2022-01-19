# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger("Delete cardmaker_export_use_license_plates")


def migrate(cr, version):
    if not version:
        return

    # Drop field "cardmaker_export_use_license_plates" from "horanet_environment_config" model
    # cause he's not used anymore
    cr.execute("DELETE FROM ir_config_parameter "
               "WHERE key = 'environment_waste_collect_cardmaker_export.use_license_plates';")
    cr.execute("DELETE FROM ir_model_fields WHERE name = 'cardmaker_export_use_license_plates';")
    cr.execute("ALTER TABLE horanet_environment_config DROP COLUMN IF EXISTS cardmaker_export_use_license_plates;")
