# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import safe_eval


class TPASmartEcoSettings(models.TransientModel):
    """TPA settings model for TPA synchronization of SmartEco system."""

    # region Private attributes
    _inherit = 'collectivity.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    tpa_smarteco_url = fields.Char(string="URL backend Smarteco")
    tpa_smarteco_is_enable = fields.Boolean(string="Is TPA smarteco enable")
    tpa_smarteco_name_method_partner = fields.Char(string="Method TPA smarteco partner")

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

    # Trick: get_default_ methods are called every time, use only one for all fields
    def get_default_tpa_smarteco_config(self, _):
        """Get default config of TPA SmartEco synchronization.

        :return configuration object
        """
        # We use safe_eval on the result, since the value of the parameter is a nonempty string
        return {
            'tpa_smarteco_url': self.get_tpa_smarteco_backend_url(),
            'tpa_smarteco_is_enable': self.get_tpa_smarteco_is_enable(),
            'tpa_smarteco_name_method_partner': self.get_tpa_smarteco_partner_method(),
        }

    # Trick: set_ methods are called every time, use only one for all fields
    def set_tpa_smarteco_config(self):
        """Set config of TPA SmartEco synchronization.

        :return nothing
        """
        self.ensure_one()

        icp = self.env['ir.config_parameter']
        # We store the repr of the values, since the value of the parameter is a required string
        icp.set_param('tpa.smarteco.backend_url', str(self.tpa_smarteco_url))
        icp.set_param('tpa.smarteco.is_enable', str(self.tpa_smarteco_is_enable))
        icp.set_param('tpa.smarteco.partner_method', self.tpa_smarteco_name_method_partner.strip())

    @api.model
    def get_tpa_smarteco_backend_url(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.smarteco.backend_url', ''))

    @api.model
    def get_tpa_smarteco_is_enable(self):
        return safe_eval(self.env['ir.config_parameter'].get_param('tpa.smarteco.is_enable', 'False'))

    @api.model
    def get_tpa_smarteco_partner_method(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.smarteco.partner_method', ''))

    # endregion

    pass
