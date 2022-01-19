# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests import common

from psycopg2 import IntegrityError


class TestArea(common.TransactionCase):

    def setUp(self):
        super(TestArea, self).setUp()

        self.area_obj = self.env['partner.contact.identification.area']

    @common.post_install(True)
    def test_create_with_name_pass(self):
        record = self.area_obj.create({'name': 'Area1'})

        self.assertEqual(record.name, 'Area1')

    @common.post_install(True)
    def test_create_with_same_name_raises_integrity_error(self):
        self.area_obj.create({'name': 'Area1'})

        with self.assertRaises(IntegrityError):
            self.area_obj.create({'name': 'Area1'})

    @common.post_install(True)
    def test_create_with_different_name_pass(self):
        record1 = self.area_obj.create({'name': 'Area1'})
        record2 = self.area_obj.create({'name': 'Area2'})

        self.assertEqual(record1.name, 'Area1')
        self.assertEqual(record2.name, 'Area2')

    @common.post_install(True)
    def test_create_with_empty_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.area_obj.create({'name': ''})

    @common.post_install(True)
    def test_create_with_only_space_in_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.area_obj.create({'name': ' '})
