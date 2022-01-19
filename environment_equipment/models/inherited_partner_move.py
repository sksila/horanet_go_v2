# coding: utf-8

from odoo import models, fields


class PartnerMoveAddAllocation(models.Model):
    u"""Ajout des allocation sur les emménagements."""

    # region Private attributes
    _inherit = 'partner.move'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    allocation_ids = fields.One2many(
        string="Allocations",
        comodel_name='partner.move.equipment.rel',
        inverse_name='move_id'
    )

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
