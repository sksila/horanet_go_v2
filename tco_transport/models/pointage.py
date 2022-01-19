# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

POINTAGE_STATUS = (
    ('0', "Ok"),
    ('1', "Rejected"),
    ('2', "Duplicate"),
    ('3', "Degraded"),
    ('4', "RFU"),
    ('5', "Manual"),
)


class Pointage(models.Model):
    """Define Pointage model."""

    # region Private attributes
    _name = 'tco.transport.pointage'
    _sql_constraints = [
        (
            'unicity_on_datetime_and_transaction_number_and_terminal_id',
            'UNIQUE(date_time, transaction_number, terminal_id)',
            _("A pointage with this datetime, transaction number and terminal id already exists.")
        )
    ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    is_valid = fields.Boolean(
        string="Valid",
        help=("The pointage is considered as valid "
              "when a minimum amount of information is provided."),
        compute='_compute_is_valid',
        store=True
    )
    status = fields.Selection(
        selection=POINTAGE_STATUS,
        help="The status of the pointage.",
        required=True
    )

    date_time = fields.Datetime(
        string="Date time",
        help="The date and time the pointage as been made.",
        required=True
    )
    vehicle_id = fields.Many2one(
        string="Vehicle",
        help="The vehicule on which the pointage as been made.",
        comodel_name='tco.transport.vehicle'
    )
    line_id = fields.Many2one(
        string="Line",
        help="The line on which the pointage as been made.",
        comodel_name='tco.transport.line'
    )
    terminal_id = fields.Many2one(
        string="Terminal",
        help="The terminal which received the pointage.",
        comodel_name='tco.terminal',
        required=True,
    )
    tag_id = fields.Many2one(
        string="Tag",
        help="The tag used to identify who made the pointage.",
        comodel_name='partner.contact.identification.tag',
    )
    partner_id = fields.Many2one(
        string="Partner",
        comodel_name='res.partner',
        help="The partner who made the pointage.",
        index=True
    )

    transaction_number = fields.Integer(
        string="Transaction number",
        help="Identifier of the pointage.",
        required=True
    )
    comment = fields.Text(
        string="Comment",
        help="Fill this field in case there are missing information."
    )
    is_locked = fields.Boolean(
        string="Locked",
        help=("The lock is activated when a billing process is associated. "
              "When the pointage is locked, no modification is possible"),
        default=False,
    )

    # endregion

    # region Fields method
    @api.multi
    @api.depends('vehicle_id', 'line_id', 'terminal_id', 'tag_id')
    def _compute_is_valid(self):
        """Check if the pointage is valid by checking its values."""
        for rec in self:
            rec.is_valid = rec.vehicle_id and rec.line_id and rec.terminal_id and rec.tag_id

    # endregion

    # region Constrains and Onchange
    @api.multi
    @api.constrains('comment')
    def _check_comment(self):
        """Check comment field shouldn't be filled only with spaces."""
        for rec in self:
            if not rec.is_valid and not rec.comment:
                raise ValidationError("A comment is required.")
            if rec.comment and len(rec.comment.strip()) == 0:
                raise ValidationError("The comment field cannot be empty.")

    @api.multi
    @api.constrains('transaction_number')
    def _check_transaction_number(self):
        """Check transaction_number field shouldn't be equal to 0."""
        for rec in self:
            if not rec.transaction_number:
                raise ValidationError("The transaction number cannot be equal to 0.")

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    def check_exists(self, pointage):
        """Check if tco.transport.pointage record already exists.

        :return: True if exists else False
        """
        rec_pointage = self.search(
            args=[
                ('date_time', '=',
                 fields.Datetime.from_string(pointage['date_time']).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                ('transaction_number', '=', pointage['transaction_number']),
                ('terminal_id', '=', pointage['terminal_id']),
            ],
            limit=1,
        )
        return True if rec_pointage else False

    # endregion

    pass
