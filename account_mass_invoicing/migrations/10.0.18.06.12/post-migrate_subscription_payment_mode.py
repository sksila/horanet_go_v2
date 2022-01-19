# coding: utf-8

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Attribute default payment method to subscriptions which don't have one."""
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Contrats sans mode de paiement
        subscriptions = env['horanet.subscription'].search([('payment_mode', '=', False)])

        subscriptions.write({
            'payment_mode': env.ref('account_mass_invoicing.payment_method_not_withdrawn').id
        })
