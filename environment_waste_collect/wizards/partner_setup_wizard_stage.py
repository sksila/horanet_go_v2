
from odoo import fields, models


class SetUpPartnerOrder(models.Model):
    u"""Wizard assistant de création de partner environnement."""

    # region Private attributes
    _name = 'partner.setup.wizard.stage'
    _order = 'order,id'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.name = fields.Char('Name', required=True, translate=True)
    order = fields.Integer(string="Order", required=True)
    view_id = fields.Many2one(string="View", comodel_name='ir.ui.view', required=True)
    # endregion

    # region Fields method
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
