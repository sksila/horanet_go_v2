# coding: utf-8

from functools import partial

from odoo.tests import common
from odoo.exceptions import ValidationError, UserError


def create(env, values={}):
    default_values = {
        'period_type': 'unlimited'
    }
    default_values.update(values)

    return env['horanet.subscription.cycle'].create(default_values)


@common.post_install(True)
class TestCycle(common.TransactionCase):

    def setUp(self):
        super(TestCycle, self).setUp()

        self.date = '2017-07-25'
        self.create = partial(create, self.env)

    def test_01_create_cycle_not_unlimited_without_quantity_fail(self):
        values = {'period_type': 'days', 'period_quantity': 0}

        with self.assertRaises(ValidationError):
            self.create(values)

    def test_02_create_with_days_pass(self):
        values = {
            'period_type': 'days',
            'period_quantity': 4
        }

        cycle = self.create(values)

        end_date = cycle.get_end_date_of_cycle(self.date)

        self.assertEqual(end_date, '2017-07-28')

    def test_03_create_with_weeks_pass(self):
        values = {
            'period_type': 'weeks',
            'period_quantity': 3
        }

        cycle = self.create(values)

        end_date = cycle.get_end_date_of_cycle(self.date)

        self.assertEqual(end_date, '2017-08-14')

    def test_04_create_with_months_pass(self):
        values = {
            'period_type': 'months',
            'period_quantity': 3
        }

        cycle = self.create(values)

        end_date = cycle.get_end_date_of_cycle(self.date)

        self.assertEqual(end_date, '2017-10-24')

    def test_05_create_with_years_pass(self):
        values = {
            'period_type': 'years',
            'period_quantity': 3
        }

        cycle = self.create(values)

        end_date = cycle.get_end_date_of_cycle(self.date)

        self.assertEqual(end_date, '2020-07-24')

    def test_08_create_pass(self):
        cycle = self.create()

        self.assertTrue(cycle.name, '1 Months')

    def test_09_get_next_day_date_with_false_value_raise_user_error(self):
        cycle = self.create()

        with self.assertRaises(UserError):
            cycle.get_next_day_date(False)
