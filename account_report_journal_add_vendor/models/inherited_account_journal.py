# -*- coding: utf-8 -*-

from odoo import models


class InheritedAccountJournal(models.AbstractModel):
    """Add vendor on journal."""

    # region Private attributes
    _inherit = 'report.account.report_journal'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    def lines(self, target_move, journal_ids, sort_selection, data):
        """Add the vendor in the context."""
        line_ids = super(InheritedAccountJournal, self).lines(target_move, journal_ids, sort_selection, data)
        if line_ids and data['form'].get('vendor_id', False):
            vendor_id = data['form']['vendor_id']
            invoices = self.env['account.invoice'].search_read([('user_id', '=', vendor_id)], ['number'])
            move_names = []
            for inv in invoices:
                move_names.append(inv.get('number'))
            if move_names:
                move_ids = self.env['account.move'].search([('name', 'in', move_names)])
                line_ids = line_ids.filtered(lambda r: r.move_id.id in move_ids.ids)
                data['form']['used_context'].update({'line_ids': line_ids.ids})

        return line_ids
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
