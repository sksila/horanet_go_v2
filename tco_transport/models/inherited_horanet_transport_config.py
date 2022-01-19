# -*- coding: utf-8 -*-

import os

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval


class InheritTransportConfig(models.TransientModel):
    """Extend Collectivity settings to add terminals configuration."""

    _inherit = 'horanet.transport.config'

    terminal_lb7_directory_path = fields.Char(
        string="Terminal LB7 directory path",
        help=("The path to use to access LB7 terminal files."),
    )
    lb7_time_offset = fields.Char(help="Value in seconds defined in timezone file of the lb7")

    @api.model
    def get_default_transport_config(self, _):
        """Return the LB7 directory path."""
        icp = self.env['ir.config_parameter']

        return {
            'terminal_lb7_directory_path': icp.get_param(
                'tco_transport.terminal_lb7_directory_path'
            ),
            'lb7_time_offset': self.get_lb7_time_offset()
        }

    @api.multi
    def set_transport_config(self):
        """Set the LB7 directory path."""
        self.ensure_one()
        icp = self.env['ir.config_parameter']

        # Check if entry is a valid absolute path before save it
        if not os.path.isabs(self.terminal_lb7_directory_path):
            raise ValidationError(_("Invalid absolute path"))

        icp.set_param('tco_transport.terminal_lb7_directory_path', self.terminal_lb7_directory_path)

    @api.multi
    def set_lb7_time_offset(self):
        self.ensure_one()

        icp = self.env['ir.config_parameter']
        icp.set_param('tco_transport.lb7_time_offset', repr(self.lb7_time_offset))

    @api.model
    def get_lb7_time_offset(self):
        icp = self.env['ir.config_parameter']
        return safe_eval(icp.get_param('tco_transport.lb7_time_offset', '14400'))
