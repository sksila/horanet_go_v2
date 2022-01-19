# -*- coding: utf-8 -*-

from odoo import api, models, fields


class HoranetTransportInscriptionConfig(models.TransientModel):
    """Add the cheque background image in horanet transport setting."""

    _inherit = 'horanet.transport.config'

    cheque_background_image = fields.Binary(
        string="Image used as background for the cheque",
        help="This image should have following dimensions: 800px width, 310px height")

    @api.model
    def get_default_inscription_config(self, _):
        """Return the URL and port of the windows service that allow medium handling."""
        ir_property_obj = self.env['ir.property']

        defaults = {'cheque_background_image': ir_property_obj.get(
            'cheque_background_image', 'horanet.transport.config')
        }
        return defaults

    @api.model
    def set_inscription_config(self):
        """Set the inscription configuration values."""
        ir_prop = self.env['ir.property']
        ir_prop.set_property_binary('cheque_background_image', self.cheque_background_image, self._name)
