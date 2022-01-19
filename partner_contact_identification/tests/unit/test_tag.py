# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests import common

from psycopg2 import IntegrityError

from utils import create_mapping


class TestTag(common.TransactionCase):

    def setUp(self):
        super(TestTag, self).setUp()

        self.tag_obj = self.env['partner.contact.identification.tag']

    @common.post_install(True)
    def test_create_with_only_number_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            self.tag_obj.create({
                'number': '1234',
            })

    @common.post_install(True)
    def test_create_with_mapping_pass(self):
        record = self.tag_obj.create({
            'number': '1234',
            'mapping_id': create_mapping(self.env, 'Tech1', 'Area1').id,
        })

        self.assertEqual(record.number, '1234')

    @common.post_install(True)
    def test_create_twice_raises_validation_error(self):
        mapping = create_mapping(self.env, 'Tech1', 'Area1')
        self.tag_obj.create({
            'number': '1234',
            'mapping_id': mapping.id,
        })

        with self.assertRaises(ValidationError):
            self.tag_obj.create({
                'number': '1234',
                'mapping_id': mapping.id,
            })

    @common.post_install(True)
    def test_create_twice_with_same_mapping_techno_and_is_csn_raises_validation_error(self):
        mapping1 = create_mapping(self.env, 'Tech1', 'Area1', 'csn')
        mapping2 = create_mapping(self.env, 'Tech1', 'Area2', 'csn')
        self.tag_obj.create({
            'number': '1234',
            'mapping_id': mapping1.id,
        })

        with self.assertRaises(ValidationError):
            self.tag_obj.create({
                'number': '1234',
                'mapping_id': mapping2.id,
            })
