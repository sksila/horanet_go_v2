# coding: utf-8

from functools import partial

from odoo.tests import common

from odoo.addons.mail.models.mail_template import format_tz

from . import test_activity


def create(env, values={}):
    action = env['horanet.action'].create({
        'name': 'Action1',
        'code': '_001',
    })
    # env.ref('horanet_subscription.action_passage').id

    device = env['horanet.device'].create({
        'name': 'Device1',
    })

    default_values = {
        'action_id': action.id,
        'device_id': device.id,
    }

    default_values.update(values)

    return env['horanet.operation'].create(default_values)


@common.post_install(True)
class TestOperation(common.TransactionCase):

    def setUp(self):
        super(TestOperation, self).setUp()

        self.create = partial(create, self.env)

    def test_01_create_operation_pass(self):

        operation = self.create()
        self.assertTrue(operation.exists())

    def test_02_get_operation_tostring_pass(self):

        operation = self.create()
        result = []
        result.append((operation.id or None, "quantity 1.0, action Action1 (_001) "))
        self.assertEqual(operation.to_string(), result)

    def test_03_get_operation_tostring_with_activity_pass(self):
        self.activity = test_activity.create(self.env)
        values = {'activity_id': self.activity.id}
        operation = self.create(values)

        result = []
        result.append((operation.id or None, "quantity 1.0, action Action1 (_001) activity Activity 1"))
        self.assertEqual(operation.to_string(), result)

    def test_04_name_get_pass(self):
        time = "2017-08-03 00:00:00"

        operation = self.create({'time': time})

        result = [(operation.id, "1.0 Action1 at %s - new" % time)]
        self.assertEqual(operation.name_get(), result)

    def test_05_compute_sale_order_line_ids_pass(self):

        operation = self.create()
        self.assertFalse(operation.sale_order_line_ids)

    def test_06_compute_display_name_pass(self):
        time = "2017-08-03 00:00:00"

        operation = self.create({'time': time})
        date = format_tz(self.env, time)
        self.assertEqual(operation.display_name, u"{}: 1.0 Action1".format(date))

    def test_07_compute_infrastructure_id_pass(self):
        operation = self.create()
        self.assertFalse(operation.infrastructure_id)
