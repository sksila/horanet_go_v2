# coding: utf-8

from ast import literal_eval
from functools import partial

from odoo.exceptions import ValidationError
from odoo.tests import common


def create(env, values={}):
    default_values = {
        'name': 'Individual',
        'domain': "[('is_company', '=', False)]",
        'code': 'INDIVIDUAL'
    }

    default_values.update(values)

    return env['subscription.category.partner'].create(default_values)


@common.post_install(True)
class TestPartnerCategory(common.TransactionCase):

    def setUp(self):
        super(TestPartnerCategory, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_with_only_space_in_name_fail(self):
        with self.assertRaises(ValidationError):
            self.create({'name': ' '})

    def test_02_create_with_only_space_in_domain_fail(self):
        with self.assertRaises(ValidationError):
            self.create({'domain': ' '})

    def test_03_get_domain_on_multiple_records_fail(self):
        individual_category = self.create()
        professional_category = self.create({
            'name': 'Professional',
            'code': 'PROFESSIONAL'
        })

        categories = self.env['subscription.category.partner'].browse(
            [individual_category.id, professional_category.id]
        )

        with self.assertRaises(ValueError):
            categories.get_domain()

    def test_04_retrieve_partners_pass(self):
        individual_category = self.create()

        partners = individual_category.partner_ids

        self.assertGreater(len(partners), 0)

    def test_05_search_category_with_admin_partner_pass(self):
        individual_category = self.create()

        searched_category = individual_category.search([
            ('partner_ids', '=', 3)
        ])

        self.assertIn(individual_category.id, searched_category.ids)

        searched_category = individual_category.search([
            ('partner_ids', 'in', [3])
        ])

        self.assertIn(individual_category.id, searched_category.ids)

    def test_06_get_domain_pass(self):
        individual_category = self.create()

        domain = individual_category.get_domain()

        self.assertEqual(literal_eval(individual_category.domain), domain)
