from odoo import models


class TPASettings(models.TransientModel):
    """TPA settings model for TPA synchronization."""

    _inherit = 'res.config.settings'
    _name = 'tpa.config.settings'
