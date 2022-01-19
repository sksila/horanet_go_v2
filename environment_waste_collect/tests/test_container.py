# -*- coding: utf-8 -*-

from odoo.tests import common


@common.post_install(True)
class TestContainer(common.TransactionCase):

    def setUp(self):
        super(TestContainer, self).setUp()

        self.container_obj = self.env['environment.container']

        waste_site = self.env['environment.waste.site'].create({
            'name': 'Warehouse1',
            'email': 'test@example.com'
        })
        self.emplacement = self.env['stock.emplacement'].create({
            'waste_site_id': waste_site.id,
            'code': 'Emplacement1'
        })

        self.container_type = self.env['environment.container.type'].create({
            'name': 'Type1',
            'volume': 12
        })

    def test_02_create_with_all_values_pass(self):
        record = self.container_obj.create({
            'name': 'Container',
            'emplacement_id': self.emplacement.id,
            'container_type_id': self.container_type.id
        })

        self.assertTrue(record.exists())

    def test_03_create_with_all_values_set_related_values(self):
        record = self.container_obj.create({
            'name': 'Container',
            'emplacement_id': self.emplacement.id,
            'container_type_id': self.container_type.id
        })

        self.assertEqual(record.activity_id.id, self.emplacement.activity_id.id)
        self.assertEqual(record.volume, self.container_type.volume)
