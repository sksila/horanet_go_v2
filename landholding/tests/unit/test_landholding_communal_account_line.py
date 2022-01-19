# coding: utf-8

from functools import partial
from . import utils
from odoo.tests import common
from psycopg2 import IntegrityError


class TestLandholdingCommunalAccountLine(common.TransactionCase):

    def setUp(self):
        super(TestLandholdingCommunalAccountLine, self).setUp()

        self.create = partial(utils.create_landholding_communal_account_line, self.env)

    def test_01_create_landholding_communal_account_pass(self):
        landholding_communal_account_line = self.create()

        self.assertTrue(landholding_communal_account_line.exists())

    def test_02_constrain_unique_name_and_city_fails(self):
        landholding_communal_account_line = self.create({
            'communal_account_id': utils.create_landholding_communal_account(self.env).id,
            'partial_label_number': '01',
        })

        with self.assertRaises(IntegrityError):
            self.create({
                'communal_account_id': landholding_communal_account_line.communal_account_id.id,
                'partial_label_number': landholding_communal_account_line.partial_label_number
            })
