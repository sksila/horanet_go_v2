# -*- coding: utf-8 -*-

__name__ = 'Delete address_state as not used anymore'


def migrate(cr, version):
    if not version:
        return

    cr.execute("DELETE FROM ir_model_fields WHERE name = 'address_state';")
    cr.execute("ALTER TABLE res_partner DROP COLUMN IF EXISTS address_state;")
    cr.execute("ALTER TABLE res_users DROP COLUMN IF EXISTS address_state;")
