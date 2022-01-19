# coding: utf-8

from functools import partial

from psycopg2 import IntegrityError

from odoo.tests import common
from odoo.exceptions import ValidationError

from .test_activity import create as create_activity


def create(env, values={}):
    activities = []
    for i in range(3):
        activities.append(create_activity(env, {'name': 'Activity %s' % i}))

    default_values = {
        'name': 'Prestation 1',
        'product_uom_categ_id': env.ref('product.product_uom_categ_unit').id,
        'activity_ids': [(6, 0, [a.id for a in activities])]
    }
    default_values.update(values)

    return env['horanet.service'].create(default_values)


@common.post_install(True)
class TestService(common.TransactionCase):

    def setUp(self):
        super(TestService, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_service_without_unit_categ_fail(self):
        values = {'product_uom_categ_id': False}

        with self.assertRaises(IntegrityError):
            self.create(values)

    def test_02_create_service_without_activities_fail(self):
        values = {'activity_ids': False}

        with self.assertRaises(ValidationError):
            self.create(values)

    def test_03_create_service_with_activities_with_different_unit_categ_fail(self):
        activities = []
        for i in range(3):
            activities.append(
                create_activity(self.env, {
                    'name': 'Activity %s' % i,
                    'product_uom_id': self.env.ref('product.product_uom_gram').id
                })
            )

        values = {'activity_ids': [(6, 0, [a.id for a in activities])]}

        with self.assertRaises(ValidationError):
            self.create(values)

    def test_04_create_service_with_activities_with_same_unit_categ_pass(self):
        activities = []
        for i in range(3):
            activities.append(
                create_activity(self.env, {
                    'name': 'Activity %s' % i,
                })
            )

        values = {'activity_ids': [(6, 0, [a.id for a in activities])]}

        service = self.create(values)

        self.assertTrue(service.exists())
