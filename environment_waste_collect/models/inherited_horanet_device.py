
from odoo import fields, models


class Ecopad(models.Model):
    u"""Surcharge des device pour y ajouter ce qui définit un Ecopad."""

    # region Private attributes
    _inherit = 'horanet.device'
    # endregion

    # region Default methods

    # endregion

    # region Fields declaration
    is_ecopad = fields.Boolean(string="Is Ecopad")

    ecopad_session_ids = fields.One2many(
        string="Sessions",
        comodel_name='environment.ecopad.session',
        inverse_name='ecopad_id',
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
