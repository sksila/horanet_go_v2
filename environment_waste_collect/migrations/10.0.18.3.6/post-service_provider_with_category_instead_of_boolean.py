# coding: utf-8

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        service_providers = env['environment.pickup.contract'].search([]) \
                                                              .mapped('service_provider_id')

        service_providers.write({
            'category_id': [
                (4, env.ref('environment_waste_collect.partner_category_service_provider').id)
            ]
        })
