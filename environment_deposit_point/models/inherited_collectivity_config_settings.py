# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.tools import safe_eval


class CollectivityContactSettings(models.TransientModel):
    """Extend Collectivity settings to add deposit point mapping."""

    _inherit = 'collectivity.config.settings'

    deposit_point_mapping_id = fields.Many2one(
        string="Deposit point support mapping",
        comodel_name='partner.contact.identification.mapping',
        help=("Set this value to use as default mapping value when "
              "launching the creation medium wizard.")
    )

    @api.model
    def get_default_deposit_point_mapping_id(self, _):
        """Return default values for identification settings.

        This return default values for deposit_point_mapping_id
        """
        icp = self.env['ir.config_parameter']

        defaults = {
            'deposit_point_mapping_id': safe_eval(icp.get_param(
                'partner_contact_identification.default_deposit_point_mapping_id', 'False'
            )),
        }
        return defaults

    @api.model
    def set_deposit_point_mapping_id(self):
        """Set the URL and port of the windows service that allow medium handling."""
        self.env['ir.config_parameter'].set_param(
            'partner_contact_identification.default_deposit_point_mapping_id',
            self.deposit_point_mapping_id.id
        )
