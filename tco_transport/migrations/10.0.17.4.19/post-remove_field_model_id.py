# -*- coding: utf-8 -*-

__name__ = 'Delete model_id field moved to model field'


def migrate(cr, version):
    if not version:
        return

    # Move values from "model_id" field to "model" field
    cr.execute("UPDATE tco_terminal "
               "SET model = 'lb7' "
               "WHERE model_id IN (SELECT id FROM tco_terminal_model WHERE UPPER(name) = 'LB7');")

    # Drop "model_id" field from "tco.terminal" model cause he's not used anymore
    cr.execute("DELETE FROM ir_model_fields WHERE model = 'tco.terminal' AND name = 'model_id';")
    cr.execute("ALTER TABLE tco_terminal DROP COLUMN IF EXISTS model_id;")

    # Drop "tco_terminal_model" model cause he's not used anymore
    cr.execute("DELETE FROM ir_model_data "
               "WHERE model = 'tco.terminal.model';")
    cr.execute("DELETE FROM ir_model_fields "
               "WHERE model = 'tco.terminal.model';")
    cr.execute("DELETE FROM ir_model WHERE name = 'tco.terminal.model';")
    cr.execute("DROP TABLE IF EXISTS tco_terminal_model;")
