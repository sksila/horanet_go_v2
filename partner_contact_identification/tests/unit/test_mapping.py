# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests import common

from psycopg2 import IntegrityError

from utils import create_area, create_technology


class TestMapping(common.TransactionCase):

    def setUp(self):
        super(TestMapping, self).setUp()

        self.mapping_obj = self.env['partner.contact.identification.mapping']

    @common.post_install(True)
    def test_create_with_only_mapping_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            self.mapping_obj.create({'mapping': 'csn'})

    @common.post_install(True)
    def test_create_with_all_values_pass(self):
        tech = create_technology(self.env, 'Tech1')
        area = create_area(self.env, 'Area1')

        record = self.mapping_obj.create({
            'mapping': 'csn',
            'technology_id': tech.id,
            'area_id': area.id
        })

        self.assertEqual(record.technology_id.id, tech.id)
        self.assertEqual(record.area_id.id, area.id)

    @common.post_install(True)
    def test_create_twice_raises_validation_error(self):
        tech = create_technology(self.env, 'Tech1')
        area = create_area(self.env, 'Area1')

        self.mapping_obj.create({
            'mapping': 'csn',
            'technology_id': tech.id,
            'area_id': area.id
        })

        with self.assertRaises(ValidationError):
            self.mapping_obj.create({
                'mapping': 'csn',
                'technology_id': tech.id,
                'area_id': area.id
            })

    @common.post_install(True)
    def test_write_with_existing_mapping_values_raises_validation_error(self):
        tech = create_technology(self.env, 'Tech1')
        area = create_area(self.env, 'Area1')

        self.mapping_obj.create({
            'mapping': 'csn',
            'technology_id': tech.id,
            'area_id': area.id
        })

        record2 = self.mapping_obj.create({
            'mapping': 'h3',
            'technology_id': tech.id,
            'area_id': area.id
        })

        with self.assertRaises(ValidationError):
            record2.write({'mapping': 'csn'})

    @common.post_install(True)
    def test_create_with_empty_mapping_raises_validation_error(self):
        tech = create_technology(self.env, 'Tech1')
        area = create_area(self.env, 'Area1')

        with self.assertRaises(IntegrityError):
            self.mapping_obj.create({
                'technology_id': tech.id,
                'area_id': area.id
            })
