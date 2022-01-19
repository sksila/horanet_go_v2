# coding: utf-8

from functools import partial

from psycopg2 import IntegrityError

from . import utils
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestDepositPoint(common.TransactionCase):

    def setUp(self):
        super(TestDepositPoint, self).setUp()

        self.create = partial(utils.create_deposit_point, self.env)

    def test_01_create_deposit_point_pass(self):
        deposit_point = self.create()

        self.assertTrue(deposit_point.exists())

    def test_02_create_deposit_without_deposit_area_fail(self):
        """Deposit point must have a deposit area to have a link to its activity sector."""
        values = {'deposit_area_id': False}

        with self.assertRaises(IntegrityError):
            self.create(values)

    def test_03_create_deposit_without_activity_fail(self):
        """Deposit point must have an activity for the creation of deposit operations."""
        values = {'activity_id': False}

        with self.assertRaises(IntegrityError):
            self.create(values)

    def test_04_create_deposit_point_activity_not_in_activity_sector_fail(self):
        """Deposit point's activity must be in deposit area's activity sector."""
        values = {'activity_id': self.env.ref('environment_waste_collect.activity_papier').id}

        with self.assertRaises(ValidationError):
            self.create(values)

    def test_05_create_deposit_point_deposit_check_point_exists(self):
        """When creating a new deposit point, a check point is automatcally created."""
        deposit_point = self.create()

        self.assertTrue(deposit_point.deposit_check_point_id.exists())
