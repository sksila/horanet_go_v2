# -*- coding: utf-8 -*-

from odoo import models, api


class VehicleTag(models.Model):
    """Extend partner.contact.identification.tag to add the notion of vehicle."""

    # region Private attributes
    _inherit = 'partner.contact.identification.tag'

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
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_vehicle(self):
        """Return vehicle."""
        return self.mapped('medium_id.vehicle_id')
    # endregion

    pass
