# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class MassInvoicingConfigSettings(models.TransientModel):
    """Add mass invoicing config in accout.config.settings."""

    # region Private attributes
    _inherit = 'account.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration

    time_of_prestation_recovery = fields.Char(
        string="Duration on which we are allowed to recover the valuation of old usages",
        default="0",
    )

    # endregion

    # region Fields method

    @api.multi
    def set_mass_invoicing_config(self):
        """Set the mass invoicing config."""
        icp = self.env['ir.config_parameter']
        icp.set_param('account_mass_invoicing.time_of_prestation_recovery', str(self.time_of_prestation_recovery))

    @api.model
    def get_default_mass_invoicing_config(self, _):
        """Get the default mass invoicing config."""
        return {
            'time_of_prestation_recovery': self.get_time_of_prestation_recovery(),
        }

    @api.model
    def get_time_of_prestation_recovery(self):
        """Get the duration on which we are allowed to recover the valuation of old usages."""
        icp = self.env['ir.config_parameter']
        return icp.get_param('account_mass_invoicing.time_of_prestation_recovery', "0")

    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions

    # endregion

    # region Model methods

    # endregion
