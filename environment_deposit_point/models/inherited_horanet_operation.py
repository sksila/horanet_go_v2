# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class DepositPointOperation(models.Model):
    # region Private attributes
    _inherit = 'horanet.operation'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    infrastructure_deposit_area_id = fields.Many2one(
        string="Deposit area",
        comodel_name='environment.deposit.area')

    deposit_point_id = fields.Many2one(
        string="Deposit point",
        comodel_name='environment.deposit.point',
        domain="[('deposit_area_id', '=?', infrastructure_deposit_area_id)]")

    # endregion

    # # region Fields method
    @api.onchange('deposit_point_id')
    def _onchange_deposit_point_id(self):
        for op in self:
            # Changer l'aire d'apports
            op.infrastructure_deposit_area_id = op.deposit_point_id.deposit_area_id

            # Changer le checkpoint
            op.check_point_id = op.deposit_point_id.deposit_check_point_id

            # Changer l'activité
            op.activity_id = op.deposit_point_id.activity_id

            # Changer l'action
            op.action_id = op.deposit_point_id.activity_id.default_action_id

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
