# coding: utf-8

from functools import partial

from psycopg2 import IntegrityError

from odoo.tests import common
from odoo.exceptions import ValidationError

from .test_service import create as create_service
from .test_cycle import create as create_cycle


def create(env, values={}):
    default_values = {
        'name': 'Prestation 1',
        'service_id': create_service(env).id,
        'is_blocked': False,
        'cycle_id': create_cycle(env).id
    }
    default_values.update(values)

    return env['horanet.prestation'].create(default_values)


@common.post_install(True)
class TestPrestation(common.TransactionCase):

    def setUp(self):
        super(TestPrestation, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_prestation_with_same_reference_fail(self):
        values = {'reference': 'A_REF'}

        prestation = self.create(values)
        self.assertTrue(prestation.exists())

        with self.assertRaises(IntegrityError):
            self.create(values)

    def test_02_create_prestation_blocked_with_balance_zero_fail(self):
        values = {
            'is_blocked': True,
            'balance': 0
        }

        with self.assertRaises(ValidationError):
            self.create(values)
