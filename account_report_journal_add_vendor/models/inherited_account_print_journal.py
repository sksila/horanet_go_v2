# -*- coding: utf-8 -*-

from odoo import models, fields


class InheritedAccountPrintJournal(models.TransientModel):
    """Add vendor on journal."""

    # region Private attributes
    _inherit = 'account.print.journal'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    vendor_id = fields.Many2one(string="Vendor", comodel_name='res.users')
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    def _print_report(self, data):
        data['form'].update({'vendor_id': self.vendor_id.id})
        data['form'].update({'vendor_name': self.vendor_id.name})
        data['form']['used_context'].update({'vendor_id': self.vendor_id.id})
        return super(InheritedAccountPrintJournal, self)._print_report(data)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
