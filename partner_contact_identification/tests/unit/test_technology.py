# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests import common

from psycopg2 import IntegrityError


class TestTechnology(common.TransactionCase):

    def setUp(self):
        super(TestTechnology, self).setUp()

        self.technology_obj = self.env['partner.contact.identification.technology']

    @common.post_install(True)
    def test_create_with_name_pass(self):
        record = self.technology_obj.create({'name': 'Tech1', 'code': 'Tech1'})

        self.assertEqual(record.name, 'Tech1')

    @common.post_install(True)
    def test_create_with_same_name_raises_integrity_error(self):
        self.technology_obj.create({'name': 'Tech1', 'code': 'Tech2'})

        with self.assertRaises(IntegrityError):
            self.technology_obj.create({'name': 'Tech1'})

    @common.post_install(True)
    def test_create_with_different_name_pass(self):
        record1 = self.technology_obj.create({'name': 'Tech1', 'code': 'Tech1'})
        record2 = self.technology_obj.create({'name': 'Tech2', 'code': 'Tech2'})

        self.assertEqual(record1.name, 'Tech1')
        self.assertEqual(record2.name, 'Tech2')

    @common.post_install(True)
    def test_create_with_empty_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.technology_obj.create({'name': '', 'code': 'u'})

    @common.post_install(True)
    def test_create_with_only_space_in_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.technology_obj.create({'name': ' ', 'code': 'u'})
