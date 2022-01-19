# coding: utf-8

from functools import partial
from . import utils
from odoo.tests import common
from psycopg2 import IntegrityError


class TestLandholdingCommunalAccount(common.TransactionCase):

    def setUp(self):
        super(TestLandholdingCommunalAccount, self).setUp()

        self.create = partial(utils.create_landholding_communal_account, self.env)

    def test_01_create_landholding_communal_account_pass(self):
        landholding_communal_account = self.create()

        self.assertTrue(landholding_communal_account.exists())

    def test_02_constrain_unique_name_and_city_fails(self):
        landholding_communal_account = self.create()

        with self.assertRaises(IntegrityError):
            self.create({
                'name': landholding_communal_account.name,
                'city_id': landholding_communal_account.city_id
            })
