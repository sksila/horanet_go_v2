
from odoo import models, fields, api, _
from odoo.addons.mail.models.mail_template import format_tz
import logging

_logger = logging.getLogger(__name__)


class Operation(models.Model):
    """Add binding to ecopad session in case of ecopad device."""

    # region Private attributes
    _inherit = 'horanet.operation'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    ecopad_transaction_id = fields.Many2one(
        string="Ecopad transaction",
        comodel_name='environment.ecopad.transaction')
    ecopad_session_id = fields.Many2one(
        string="Ecopad session",
        related='ecopad_transaction_id.ecopad_session_id',
        readonly=True)
    ecopad_session_guardian_id = fields.Many2one(
        string="Ecopad session guardian",
        related='ecopad_session_id.guardian_id',
        readonly=True)
    ecopad_session_waste_site_id = fields.Many2one(
        string="Ecopad session wastesite",
        related='ecopad_session_id.waste_site_id',
        readonly=True)
    infrastructure_waste_site_id = fields.Many2one(
        string="Infrastructure wastesite",
        comodel_name='environment.waste.site',
        compute='compute_infrastructure_waste_site_id',
        readonly=True)

    # endregion

    # region Fields method
    @api.multi
    def compute_infrastructure_waste_site_id(self):
        for op in self:
            ws = False
            if op.infrastructure_id:
                ws = op.infrastructure_waste_site_id.search(
                    [('infrastructure_id', '=', op.infrastructure_id.id)], limit=1)
            op.infrastructure_waste_site_id = ws and ws.id

    @api.multi
    def compute_display_name(self):
        super(Operation, self).compute_display_name()
        for op in self:
            if op.action_id.code == "DEPOT":
                op.display_name = _(u"Deposit of {} {} of waste ({})").format(op.quantity,
                                                                              op.activity_id.product_uom_id.name,
                                                                              op.activity_id.name)
            elif op.action_id.code == "PASS":
                op_date = format_tz(self.env, op.time)
                op.display_name = _(u"Access on {}").format(op_date)

    @api.depends('ecopad_session_id')
    def _compute_infrastructure_id(self):
        super(Operation, self)._compute_infrastructure_id()

        for rec in self.filtered('ecopad_session_id'):
            rec.infrastructure_id = rec.ecopad_session_id.waste_site_id.infrastructure_id.id

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
