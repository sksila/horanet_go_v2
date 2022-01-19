# -*- coding: utf-8 -*-

from odoo.tests import common
from odoo.exceptions import ValidationError

from psycopg2 import IntegrityError

from utils import create_assignation, create_partner, create_tag


class TestMedium(common.TransactionCase):

    def _create_mapping(self):
        mapping_obj = self.env['partner.contact.identification.mapping']

        tech = self.env['partner.contact.identification.technology'].create({
            'name': 'Tech1'
        })
        area = self.env['partner.contact.identification.area'].create({
            'name': 'Area1'
        })

        return mapping_obj.create({
            'mapping': 'csn',
            'technology_id': tech.id,
            'area_id': area.id
        })

    def setUp(self):
        super(TestMedium, self).setUp()

        self.medium_obj = self.env['partner.contact.identification.medium']
        self.type = self.env['partner.contact.identification.medium.type'].create({
            'name': 'Type1'
        })
        self.tag = self.env['partner.contact.identification.tag'].create({
            'number': '1234',
            'mapping_id': self._create_mapping().id
        })

    def test_create_with_only_tag_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            self.medium_obj.create({
                'tag_ids': self.tag.id,
            })

    def test_create_with_all_values_pass(self):
        record = self.medium_obj.create({
            'type_id': self.type.id,
            'tag_ids': [(6, 0, [self.tag.id])],
        })

        self.assertEqual(record.type_id.id, self.type.id)
        self.assertEqual(record.tag_ids[0].id, self.tag.id)

    def test_create_with_tags_from_different_partner_raises_validation_error(self):
        """We shouldn't allow tags assigned to different partners on the same medium."""
        tag1 = create_tag(self.env, {'number': '1234'})
        tag2 = create_tag(self.env, {'number': '4567'})

        partner1 = create_partner(self.env, 'Partner1')
        partner2 = create_partner(self.env, 'Partner2')

        create_assignation(self.env, {
            'reference_id': 'res.partner,%s' % partner1.id,
            'tag_id': tag1.id
        })
        create_assignation(self.env, {
            'reference_id': 'res.partner,%s' % partner2.id,
            'tag_id': tag2.id
        })

        with self.assertRaises(ValidationError):
            self.medium_obj.create({
                'type_id': self.type.id,
                'tag_ids': [(6, 0, [tag1.id, tag2.id])]
            })
