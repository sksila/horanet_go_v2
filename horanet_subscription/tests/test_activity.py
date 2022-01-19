# coding: utf-8

from functools import partial

from psycopg2 import IntegrityError

from odoo.tests import common


def create(env, values={}):
    default_values = {
        'name': 'Activity 1',
        'product_uom_id': env.ref('product.product_uom_unit').id,
        'default_action_id': env.ref('horanet_subscription.action_passage').id
    }

    default_values.update(values)

    return env['horanet.activity'].create(default_values)


@common.post_install(True)
class TestActivity(common.TransactionCase):

    def setUp(self):
        super(TestActivity, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_activity_without_unit_fail(self):
        values = {'product_uom_id': False}

        with self.assertRaises(IntegrityError):
            self.create(values)

    def test_02_create_activity_with_same_reference_fail(self):
        values = {'reference': 'A_REF'}
        activity = self.create(values)

        self.assertTrue(activity.exists())

        with self.assertRaises(IntegrityError):
            self.create(values)

    def test_03_create_activity_without_action_fail(self):
        values = {'default_action_id': False}

        with self.assertRaises(IntegrityError):
            self.create(values)

    def test_04_create_activity_pass(self):
        activity = self.create()

        self.assertTrue(activity.exists())
        self.assertTrue(activity.product_uom_categ_id.exists())
