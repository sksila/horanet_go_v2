# coding: utf-8

from functools import partial

from odoo.tests import common

from . import test_activity


def create(env, values={}):

    default_values = {
        'quantity': 1.0,
        'activity_id': test_activity.create(env).id,
    }

    default_values.update(values)

    return env['horanet.usage'].create(default_values)


@common.post_install(True)
class TestUsage(common.TransactionCase):

    def setUp(self):
        super(TestUsage, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_usage_pass(self):

        usage = self.create()
        self.assertTrue(usage.exists())

    def test_02_get_usage_tostring_pass(self):
        usage = self.create()
        result = []
        result.append((usage.id or None, "quantity 1.0, activity Activity 1 not linked to a contract line"))
        self.assertEqual(usage  .to_string(), result)
