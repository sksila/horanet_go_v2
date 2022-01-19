# -*- coding: utf-8 -*-

import logging

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class HoranetTerminalLB7Log(models.Model):
    """Specific class for LB7 Terminal."""

    # region Private attributes
    _name = 'tco.terminal.lb7.log'
    _inherits = {'auditlog.log': 'log_id'}
    _inherit = 'ir.needaction_mixin'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    log_id = fields.Many2one(
        string='Log',
        comodel_name='auditlog.log',
        required=True,
        ondelete='cascade',
        delegate=True,
    )
    message = fields.Text(
        string="Message",
        help="Message from process"
    )
    is_error = fields.Boolean(
        string="Is error",
        default=False,
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.model
    def _needaction_domain_get(self):
        return [('is_error', '=', True)]

    # endregion

    # region Model methods
    # endregion

    pass
