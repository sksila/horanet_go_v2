# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests import common


@common.post_install(True)
class TestPickupRequest(common.TransactionCase):

    def setUp(self):
        super(TestPickupRequest, self).setUp()

        self.pickup_request_model = self.env['environment.pickup.request']

        waste_site = self.env['environment.waste.site'].create({
            'name': 'waste_site1',
            'email': 'test@example.com'
        })
        waste = self.env['horanet.activity'].create({
            'name': 'Bois',
            'default_action_id': self.env.ref('environment_waste_collect.horanet_action_depot').id,
            'product_uom_id': self.env.ref('environment_waste_collect.m3_product_uom').id
        })
        provider = self.env['res.partner'].create({
            'name': 'Service provider',
            'category_id': [(4, self.env.ref('environment_waste_collect.partner_category_service_provider').id)]
        })

        self.env['environment.pickup.contract'].create({
            'waste_site_id': waste_site.id,
            'activity_ids': [(6, 0, [waste.id])],
            'service_provider_id': provider.id
        })

        self.emplacement = self.env['stock.emplacement'].create({
            'waste_site_id': waste_site.id,
            'code': 'E1',
            'activity_id': waste.id
        })

    def test_01_create_two_on_same_emplacement_raise_validation_error(self):
        record = self.pickup_request_model.create({
            'name': 'A name',
            'emplacement_id': self.emplacement.id
        })

        self.assertTrue(record.exists())

        with self.assertRaises(ValidationError):
            self.pickup_request_model.create({
                'name': 'Another name',
                'emplacement_id': self.emplacement.id
            })

    def test_02_create_without_name_pass(self):
        record = self.pickup_request_model.create({'emplacement_id': self.emplacement.id})

        self.assertTrue(record.exists())
