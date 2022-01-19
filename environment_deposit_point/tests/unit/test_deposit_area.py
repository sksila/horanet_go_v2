# coding: utf-8

from functools import partial
from . import utils
from odoo.tests import common


class TestDepositArea(common.TransactionCase):

    def setUp(self):
        super(TestDepositArea, self).setUp()

        self.create = partial(utils.create_deposit_area, self.env)

    def test_01_create_deposit_area_pass(self):
        deposit_area = self.create()

        self.assertTrue(deposit_area.exists())
