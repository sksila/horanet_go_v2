# -*- coding: utf-8 -*-

from functools import partial

from odoo.exceptions import ValidationError
from odoo.tests import common

from .test_waste_site import create as create_waste_site


def create(env, values={}):
    service_provider_category = env.ref('environment_waste_collect.partner_category_service_provider')
    service_provider = env['res.partner'].create({
        'name': 'A provider 1',
        'category_id': [(4, service_provider_category.id)]
    })
    default_values = {
        'name': 'Contract 1',
        'service_provider_id': service_provider.id,
        'waste_site_id': create_waste_site(env).id
    }

    default_values.update(values)

    return env['environment.pickup.contract'].create(default_values)


@common.post_install(True)
class TestPickupContract(common.TransactionCase):

    def setUp(self):
        super(TestPickupContract, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_with_values_pass(self):
        """We should be able to create a contract linked to a waste_site."""
        record = self.create()

        self.assertTrue(record.exists())

    def test_02_create_two_on_same_waste_site_with_same_product_fail(self):
        """Don't allow two contracts on same waste_site and same waste."""
        waste = self.env['horanet.activity'].create({
            'name': 'Bois',
            'default_action_id': self.env.ref('environment_waste_collect.horanet_action_depot').id,
            'product_uom_id': self.env.ref('environment_waste_collect.m3_product_uom').id
        })
        waste_site = create_waste_site(self.env)

        record = self.create({
            'activity_ids': [(4, [waste.id])],
            'waste_site_id': waste_site.id
        })
        self.assertTrue(record.exists())

        with self.assertRaises(ValidationError):
            self.create({
                'name': 'Contract 2',
                'activity_ids': [(4, [waste.id])],
                'waste_site_id': waste_site.id
            })
