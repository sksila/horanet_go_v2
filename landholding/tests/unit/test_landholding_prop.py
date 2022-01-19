# coding: utf-8

from functools import partial
from . import utils
from odoo.tests import common
from psycopg2 import IntegrityError


class TestLandholdingProp(common.TransactionCase):

    def setUp(self):
        super(TestLandholdingProp, self).setUp()

        self.create = partial(utils.create_landholding_prop, self.env)

    def test_01_create_landholding_prop_pass(self):
        landholding_prop = self.create()

        self.assertTrue(landholding_prop.exists())

    def test_02_constrain_majic_person_number_fails(self):
        self.create({'majic_person_number': 'ZZZ999'})

        with self.assertRaises(IntegrityError):
            self.create({'majic_person_number': 'ZZZ999'})
