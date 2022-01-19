# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests import common

from psycopg2 import IntegrityError


@common.post_install(True)
class TestContainerType(common.TransactionCase):

    def setUp(self):
        super(TestContainerType, self).setUp()

        self.container_type_obj = self.env['environment.container.type']

    def test_01_create_with_name_pass(self):
        record = self.container_type_obj.create({'name': 'Type1'})

        self.assertEqual(record.name, 'Type1')

    def test_02_create_without_name_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            self.container_type_obj.create({})

    def test_03_create_with_empty_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.container_type_obj.create({'name': ''})

    def test_04_create_with_only_spaces_in_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.container_type_obj.create({'name': '  '})

    def test_05_create_with_volume_pass(self):
        record = self.container_type_obj.create({
            'name': 'Type1',
            'volume': 12
        })

        self.assertTrue(record.exists())

    def test_06_create_with_empty_volume_pass(self):
        record = self.container_type_obj.create({'name': 'Type1', 'volume': ''})

        self.assertTrue(record.exists())
