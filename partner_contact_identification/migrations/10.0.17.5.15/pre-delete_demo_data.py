# coding: utf-8


def migrate(cr, version):
    """Rename old technology demo Mifare."""
    if not version:
        return

    cr.execute("UPDATE PARTNER_CONTACT_IDENTIFICATION_TECHNOLOGY SET NAME = 'Demo Mifare' WHERE NAME = 'Mifare'")
