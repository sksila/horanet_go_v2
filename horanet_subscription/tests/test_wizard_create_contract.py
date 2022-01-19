# coding: utf-8

from odoo.tests import common

from .test_contract_template import create as create_contract_template


@common.post_install(True)
class TestContractTemplate(common.TransactionCase):

    def setUp(self):
        super(TestContractTemplate, self).setUp()

        self.create_contract_model = self.env['subscription.wizard.create.contract']

    def test_01_create_contract_for_partner_pass(self):
        import datetime
        now = datetime.datetime.now()

        template = create_contract_template(self.env, 'individual')
        wizard = self.create_contract_model.create({
            'subscription_template_id': template.id
        })
        partner = self.env['res.partner'].create({'name': 'A Partner'})

        wizard.create_contract(partner)

        subscription = self.env['horanet.subscription'].search([
            ('client_id', '=', partner.id)
        ])

        self.assertTrue(subscription.exists())

        for package_line in subscription.package_ids.mapped('line_ids'):
            end_date = package_line.package_id.cycle_id.get_end_date_of_cycle(package_line.start_date)

            self.assertEqual(package_line.end_date, end_date)
            self.assertEqual(package_line.state, 'active')

        # Based on the fact that our subscription has two packages with a cycle
        # of one year, we assume that 3 years later, we'll have
        # - 3 subscription lines
        # - 8 package lines
        subscription.compute_subscription(str(now.year + 3) + '-03-01')

        self.assertEqual(len(subscription.line_ids), 3)
        self.assertEqual(len(subscription.package_ids.mapped('line_ids')), 6)
