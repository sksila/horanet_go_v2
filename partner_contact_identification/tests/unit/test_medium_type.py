# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests import common

from psycopg2 import IntegrityError


class TestMediumType(common.TransactionCase):

    def setUp(self):
        super(TestMediumType, self).setUp()

        self.medium_type_obj = self.env['partner.contact.identification.medium.type']

    @common.post_install(True)
    def test_create_with_name_pass(self):
        record = self.medium_type_obj.create({'name': 'MedType1'})

        self.assertEqual(record.name, 'MedType1')

    @common.post_install(True)
    def test_create_with_same_name_raises_integrity_error(self):
        self.medium_type_obj.create({'name': 'MedType1'})

        with self.assertRaises(IntegrityError):
            self.medium_type_obj.create({'name': 'MedType1'})

    @common.post_install(True)
    def test_create_with_different_name_pass(self):
        record1 = self.medium_type_obj.create({'name': 'MedType1'})
        record2 = self.medium_type_obj.create({'name': 'MedType2'})

        self.assertEqual(record1.name, 'MedType1')
        self.assertEqual(record2.name, 'MedType2')

    @common.post_install(True)
    def test_create_with_empty_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.medium_type_obj.create({'name': ''})

    @common.post_install(True)
    def test_create_with_only_space_in_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.medium_type_obj.create({'name': ' '})
