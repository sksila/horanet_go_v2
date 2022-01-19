import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class TPASynchronizationCardAssignation(models.Model):
    """Assign a tag to a partner for some duration."""

    # region Private attributes
    _inherit = 'partner.contact.identification.assignation'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    last_sync_date = fields.Datetime(string="DateTime last synchronization")
    last_message_export = fields.Text(string="Export message")
    is_up_to_date = fields.Boolean(string="Is up to date", compute='_compute_is_up_to_date', store=True)
    try_number = fields.Integer(string="Number of tries since last export")
    last_sync_try = fields.Datetime(string="DateTime last try of synchronization")

    # endregion

    # region Fields method
    @api.multi
    @api.depends('write_date', 'last_sync_date')
    def _compute_is_up_to_date(self):
        for rec in self:
            rec.is_up_to_date = rec.write_date <= rec.last_sync_date

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
