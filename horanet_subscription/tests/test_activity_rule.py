# coding: utf-8

from functools import partial

from odoo.tests import common

from . import test_activity


def create(env, values={}):

    default_values = {
        'name': "Rule 1",
    }

    default_values.update(values)

    return env['activity.rule'].create(default_values)


@common.post_install(True)
class TestActivityRule(common.TransactionCase):

    def setUp(self):
        super(TestActivityRule, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_rule_pass(self):

        rule = self.create()
        self.assertTrue(rule.exists())

    def test_02_compute_state_active_pass(self):
        rule = self.create()
        self.assertTrue(rule.state == 'active')

    def test_03_compute_state_disabled_pass(self):
        rule = self.create()

        rule.action_deactivate()
        self.assertTrue(rule.state == 'disabled')

    def test_04_compute_state_deactivate_activate_pass(self):
        rule = self.create()

        rule.action_deactivate()
        rule.action_activate()
        self.assertTrue(rule.state == 'active')

    def test_05_compute_state_inactive_begin_date_pass(self):
        begin = "2030-01-01 00:00:00"
        rule = self.create({'beginning_date': begin})
        self.assertTrue(rule.state == 'inactive')

    def test_06_compute_state_inactive_end_date_pass(self):
        begin = "2017-01-01 00:00:00"
        end = "2017-01-10 00:00:00"
        rule = self.create({'beginning_date': begin,
                            'ending_date': end})
        self.assertTrue(rule.state == 'inactive')

    def test_07_name_get_pass(self):
        code = "RULE001"

        rule = self.create({'code': code})

        # Doit renvoyer : [(rule.id, rule.name + ' (' + rule.code + ') v' + str(rule.version))]
        result = [(rule.id, 'Rule 1 (RULE001) v1')]

        self.assertEqual(rule.name_get(), result)

    def test_08_resolve_rule_execution_plan_with_wrong_activity_fail(self):

        rule = self.create()

        with self.assertRaises(TypeError):
            rule.resolve_rule_execution_plan("Wrong activity")

    def test_09_resolve_rule_execution_plan_with_wrong_sector_fail(self):
        self.activity = test_activity.create(self.env)

        rule = self.create()

        with self.assertRaises(TypeError):
            rule.resolve_rule_execution_plan(self.activity, sector="Wrong sector")
