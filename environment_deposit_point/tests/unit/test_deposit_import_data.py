# coding: utf-8

from functools import partial

from psycopg2 import IntegrityError

from . import utils
from odoo.tests import common

try:
    from odoo.addons.partner_contact_identification.tests.unit.utils import create_tag
except ImportError:
    from partner_contact_identification.tests.unit.utils import create_tag


class TestDepositImportData(common.TransactionCase):

    def setUp(self):
        super(TestDepositImportData, self).setUp()

        self.create = partial(utils.create_deposit_import_data, self.env)

    def test_01_create_deposit_import_data_pass(self):
        deposit_import_data = self.create()

        self.assertTrue(deposit_import_data.exists())

    def test_02_create_deposit_import_data_no_code_fail(self):
        values = {'code': False}

        with self.assertRaises(IntegrityError):
            self.create(values)

    def test_03_create_deposit_import_data_no_data_fail(self):
        values = {'data': False}

        with self.assertRaises(IntegrityError):
            self.create(values)

    def test_04_create_deposit_import_data_duplicate_code_fail(self):
        """Import code must be unique.

        In case of import error, we may receive the same data twice.
        In this case, we update the import record based on its code
        """
        self.create()

        with self.assertRaises(IntegrityError):
            self.create()

    def test_05_create_deposit_import_data_process_fail(self):
        """If the data is not in the right format, processing data makes import turn to 'error' state."""
        values = {'data': '[{"serial_number": "2017-10-02 12:46:00"}]'}

        deposit_import_data = self.create(values)
        deposit_import_data.action_process_data()

        self.assertTrue(deposit_import_data.state == 'error')
        self.assertTrue(deposit_import_data.errors)

    def test_06_create_deposit_import_data_process_pass(self):
        """If the data is in the right format, processing data makes import turn to 'processed' state."""
        deposit_import_data = self.create()
        deposit_import_data.action_process_data()

        self.assertTrue(deposit_import_data.state == 'processed')
        self.assertFalse(deposit_import_data.errors)

    def test_07_create_deposit_import_data_process_operation_created(self):
        """After processing the data, verify in the operation has been created."""
        deposit_point = utils.create_deposit_point(self.env)
        tag = create_tag(self.env, "123456789")

        values = {
            'deposit_point': deposit_point,
            'tag': tag
        }

        deposit_import_data = self.create(values)
        deposit_import_data.action_process_data()

        operation = self.env['horanet.operation'].search([
            ('quantity', '=', 1),
            ('action_id', '=', deposit_point.activity_id.default_action_id.id),
            ('tag_id', '=', tag.id),
            ('activity_id', '=', deposit_point.activity_id.id),
            ('check_point_id', '=', deposit_point.deposit_check_point_id.id),
            ('time', '=', "2017-10-02 12:46:00"),
        ])

        self.assertTrue(operation.exists())
