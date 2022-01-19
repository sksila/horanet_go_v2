# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.tools.safe_eval import safe_eval


class InheritedAccountMoveLine(models.Model):

    # region Private attributes
    _inherit = 'account.move.line'
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
    @api.model
    def _query_get(self, domain=None):
        """Add ids of move lines if there is a vendor in the context."""
        context = dict(self._context or {})
        domain = domain or []
        if not isinstance(domain, (list, tuple)):
            domain = safe_eval(domain)

        if context.get('vendor_id', False):
            domain += [('id', 'in', context.get('line_ids', []))]

        return super(InheritedAccountMoveLine, self)._query_get(domain)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
