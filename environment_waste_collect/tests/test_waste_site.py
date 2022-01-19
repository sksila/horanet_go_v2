# coding: utf-8

from functools import partial

from odoo.tests import common


def create(env, values={}):
    default_values = {
        'name': 'Waste Site 1',
        'email': 'test@example.com'
    }

    default_values.update(values)

    return env['environment.waste.site'].create(default_values)


@common.post_install(True)
class TestWasteSite(common.TransactionCase):

    def setUp(self):
        super(TestWasteSite, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_pass(self):
        record = self.create()

        self.assertTrue(record.exists())

    def test_02_create_with_guardian_pass(self):
        """Create a guardian and check that his added to guardian list."""
        guardian = self.env['res.partner'].create({
            'name': 'Guardian 1',
            'category_id': [(4, self.env.ref('environment_waste_collect.partner_category_guardian').id)]
        })

        record = self.create()

        self.assertIn(guardian, record.partner_guardian_ids)
