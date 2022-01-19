# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.tools import safe_eval


class TPASmartBambiSettings(models.TransientModel):
    """TPA settings model for TPA synchronization of SmartBambi system."""

    # region Private attributes
    _inherit = 'collectivity.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    tpa_smartbambi_url = fields.Char(string="URL backend SmartBambi")
    tpa_smartbambi_is_enable = fields.Boolean(string="Is TPA SmartBambi enable")
    tpa_smartbambi_name_method_partner = fields.Char(string="Method backend SmartBambi")

    tpa_smartbambi_other_url = fields.Char(string="URL backend Other SmartBambi")
    tpa_smartbambi_is_other_enable = fields.Boolean(string="Is other TPA SmartBambi enable")
    tpa_smartbambi_name_method_other_partner = fields.Char(string="Method backend other SmartBambi")

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
    @api.model
    def get_default_tpa_smartbambi_config(self, _):
        """Get default config of TPA SmartBambi synchronization.

        :return configuration object
        """
        # We use safe_eval on the result, since the value of the parameter is a nonempty string
        return {
            'tpa_smartbambi_url': self.get_tpa_smartbambi_backend_url(),
            'tpa_smartbambi_is_enable': self.get_tpa_smartbambi_is_enable(),
            'tpa_smartbambi_name_method_partner': self.get_tpa_smartbambi_partner_method(),
            'tpa_smartbambi_other_url': self.get_tpa_smartbambi_backend_other_url(),
            'tpa_smartbambi_is_other_enable': self.get_tpa_smartbambi_is_other_enable(),
            'tpa_smartbambi_name_method_other_partner': self.get_tpa_smartbambi_other_partner_method(),
        }

    # Trick: set_ methods are called every time, use only one for all fields
    @api.multi
    def set_tpa_smartbambi_config(self):
        """Set config of TPA SmartBambi synchronization.

        :return nothing
        """
        self.ensure_one()

        icp = self.env['ir.config_parameter']
        # We store the repr of the values, since the value of the parameter is a required string
        icp.set_param('tpa.smartbambi.backend_url', self.tpa_smartbambi_url.strip())
        icp.set_param('tpa.smartbambi.is_enable', str(self.tpa_smartbambi_is_enable))
        icp.set_param('tpa.smartbambi.partner_method', self.tpa_smartbambi_name_method_partner.strip())

        icp.set_param('tpa.smartbambi.backend_other_url', self.tpa_smartbambi_other_url.strip())
        icp.set_param('tpa.smartbambi.is_other_enable', str(self.tpa_smartbambi_is_other_enable))
        icp.set_param('tpa.smartbambi.other_partner_method', self.tpa_smartbambi_name_method_other_partner.strip())

    @api.model
    def get_tpa_smartbambi_backend_url(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.smartbambi.backend_url', ''))

    @api.model
    def get_tpa_smartbambi_backend_other_url(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.smartbambi.backend_other_url', ''))

    @api.model
    def get_tpa_smartbambi_is_other_enable(self):
        return safe_eval(self.env['ir.config_parameter'].get_param('tpa.smartbambi.is_other_enable', 'False'))

    @api.model
    def get_tpa_smartbambi_is_enable(self):
        return safe_eval(self.env['ir.config_parameter'].get_param('tpa.smartbambi.is_enable', 'False'))

    @api.model
    def get_tpa_smartbambi_other_partner_method(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.smartbambi.other_partner_method', ''))

    @api.model
    def get_tpa_smartbambi_partner_method(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.smartbambi.partner_method', ''))

    # endregion

    pass
