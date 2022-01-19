# coding: utf-8

from functools import partial
from . import utils
from odoo.tests import common
from psycopg2 import IntegrityError


class TestLandholdingBati(common.TransactionCase):

    def setUp(self):
        super(TestLandholdingBati, self).setUp()

        self.create = partial(utils.create_landholding_bati, self.env)

    def test_01_create_landholding_bati_pass(self):
        landholding_bati = self.create()

        self.assertTrue(landholding_bati.exists())

    def test_02_constrain_unique_id_fails(self):
        self.create()

        with self.assertRaises(IntegrityError):
            self.create()
