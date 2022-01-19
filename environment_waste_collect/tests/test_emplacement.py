# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests import common

from psycopg2 import IntegrityError


@common.post_install(True)
class TestEmplacement(common.TransactionCase):

    def setUp(self):
        super(TestEmplacement, self).setUp()

        self.emplacement_obj = self.env['stock.emplacement']
        self.waste_site = self.env['environment.waste.site'].create({
            'name': 'waste_site1',
            'email': 'test@example.com'
        })

    def test_01_create_without_wharehouse_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            self.emplacement_obj.create({'code': 'Code1'})

    def test_02_create_without_code_raises_integrity_error(self):
        with self.assertRaises(ValidationError):
            self.emplacement_obj.create({
                'waste_site_id': self.waste_site.id,
                'code': ''
            })

    def test_03_create_with_only_spaces_in_code_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.emplacement_obj.create({
                'waste_site_id': self.waste_site.id,
                'code': '  '
            })

    def test_04_create_with_values_pass(self):
        record = self.emplacement_obj.create({
            'waste_site_id': self.waste_site.id,
            'code': 'Emplacement1'
        })

        self.assertTrue(record.exists())
        self.assertEqual(record.waste_site_id.id, self.waste_site.id)

    def test_05_create_with_invalid_filling_level_reset_it(self):
        record = self.emplacement_obj.create({
            'waste_site_id': self.waste_site.id,
            'code': 'Emplacement1',
            'filling_level': -25
        })
        self.assertEqual(record.filling_level, 0)

        record = self.emplacement_obj.create({
            'waste_site_id': self.waste_site.id,
            'code': 'Emplacement2',
            'filling_level': 125
        })
        self.assertEqual(record.filling_level, 100)
