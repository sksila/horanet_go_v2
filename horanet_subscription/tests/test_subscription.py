# coding: utf-8

from odoo.tests import common

from .test_contract_template import create as create_contract_template


@common.post_install(True)
class TestSubscription(common.TransactionCase):

    def setUp(self):
        super(TestSubscription, self).setUp()

        self.subscription_model = self.env['horanet.subscription']

    def test_01_create_renewable_subscription_set_rights_dates(self):
        import datetime
        now = datetime.datetime.now()
        from ..tools import date_utils
        from odoo import fields

        opening_date = str(now.year) + '-03-01 00:00:00'
        subscription_template_renewable = create_contract_template(self.env, 'individual_renewable')

        partner = self.env['res.partner'].create({'name': 'A Partner'})

        subscription = self.subscription_model.create_subscription(
            [partner.id],
            subscription_template_renewable.id,
            opening_date
        )

        self.assertTrue(subscription.exists())
        self.assertEqual(len(subscription.line_ids), 1)

        # Check dates of the line
        self.assertEqual(subscription.line_ids.start_date, subscription.start_date)
        self.assertEqual(subscription.line_ids.end_date, subscription.end_date)
        self.assertEqual(subscription.line_ids.opening_date, subscription.opening_date)

        line_closing_date = fields.Datetime.to_string(
            date_utils.convert_date_to_closing_datetime(
                subscription.cycle_id.get_end_date_of_cycle(opening_date)))
        self.assertEqual(subscription.line_ids.closing_date, line_closing_date)

        # We set the opening date of the subscription on the last year
        opening_date = str(now.year-1) + '-07-01 00:00:00'
        subscription.opening_date = opening_date

        subscription.compute_subscription(opening_date)

        self.assertEqual(len(subscription.line_ids), 2)
        lines = subscription.line_ids.sorted('start_date')

        # Check dates of first line
        self.assertEqual(lines[0].start_date, subscription.start_date)
        self.assertEqual(lines[0].opening_date, opening_date)

        line_end_date = subscription.cycle_id.get_end_date_of_cycle(lines[0].start_date)
        self.assertEqual(lines[0].end_date, line_end_date)

        line_closing_date = fields.Datetime.to_string(
            date_utils.convert_date_to_closing_datetime(
                subscription.cycle_id.get_end_date_of_cycle(lines[0].opening_date)))
        self.assertEqual(lines[0].closing_date, line_closing_date)

        # Check dates of second line
        self.assertEqual(lines[1].opening_date, str(now.year) + '-01-01 00:00:00')

        line_end_date = subscription.cycle_id.get_end_date_of_cycle(lines[1].start_date)
        self.assertEqual(lines[1].end_date, line_end_date)

        self.assertEqual(lines[1].end_date, subscription.end_date)

        # We now set the closing date of the subscription
        # This should set the closing date of the last line to subscription closing date
        closing_date = str(now.year) + '-08-01 10:59:59'
        subscription.closing_date = closing_date

        subscription.compute_subscription()

        self.assertEqual(len(subscription.line_ids), 2)
        lines = subscription.line_ids.sorted('start_date')

        self.assertEqual(lines[1].closing_date, subscription.closing_date)
