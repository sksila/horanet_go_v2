# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.tools import safe_eval


class TPAAquaglissSettings(models.TransientModel):
    """TPA settings model for TPA synchronization of Aquagliss system."""

    # region Private attributes
    _inherit = 'collectivity.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    tpa_aquagliss_url = fields.Char(string="URL backend Aquagliss")
    tpa_aquagliss_is_enable = fields.Boolean(string="Is TPA Aquagliss enable")
    tpa_aquagliss_name_method_partner = fields.Char(string="Method backend Aquagliss")

    # Setting for synchonisation of cards Aquagliss
    tpa_aquagliss_cards_is_enable = fields.Boolean(string="Send Card Cards to Aquagliss")
    tpa_aquagliss_assignation_cards_enable = fields.Boolean(string="Send Cards to Aquagliss with assignation")
    tpa_aquagliss_name_method_card = fields.Char(string="Method backend cards Aquagliss")
    tpa_aquagliss_technologies_card = fields.Char(string="Match technologies cards Aquagliss")
    tpa_aquagliss_categories_card = fields.Char(string="Match categories cards Aquagliss")

    tpa_aquagliss_area = fields.Many2one(comodel_name='partner.contact.identification.area', string="Aera Aquagliss")

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
    def get_default_tpa_aquagliss_config(self, _):
        """Get default config of TPA Aquagliss synchronization.

        :return configuration object
        """
        # We use safe_eval on the result, since the value of the parameter is a nonempty string
        return {
            'tpa_aquagliss_url': self.get_tpa_aquagliss_backend_url(),
            'tpa_aquagliss_is_enable': self.get_tpa_aquagliss_is_enable(),
            'tpa_aquagliss_name_method_partner': self.get_tpa_aquagliss_partner_method(),
            'tpa_aquagliss_cards_is_enable': self.get_tpa_aquagliss_cards_is_enable(),
            'tpa_aquagliss_assignation_cards_enable': self.get_tpa_aquagliss_assignation_cards_enable(),
            'tpa_aquagliss_name_method_card': self.get_tpa_aquagliss_name_method_card(),
            'tpa_aquagliss_technologies_card': self.get_tpa_aquagliss_technologies_card(),
            'tpa_aquagliss_categories_card': self.get_tpa_aquagliss_categories_card(),
            'tpa_aquagliss_area': self.get_tpa_aquagliss_area(),
        }

    # Trick: set_ methods are called every time, use only one for all fields
    @api.multi
    def set_tpa_aquagliss_config(self):
        """Set config of TPA Aquagliss synchronization.

        :return nothing
        """
        self.ensure_one()

        icp = self.env['ir.config_parameter']
        # We store the repr of the values, since the value of the parameter is a required string
        icp.set_param('tpa.aquagliss.backend_url', self.tpa_aquagliss_url.strip())
        icp.set_param('tpa.aquagliss.is_enable', str(self.tpa_aquagliss_is_enable))
        icp.set_param('tpa.aquagliss.partner_method', self.tpa_aquagliss_name_method_partner.strip())
        icp.set_param('tpa.aquagliss.cards_is_enable', str(self.tpa_aquagliss_cards_is_enable))
        icp.set_param('tpa.aquagliss.assignation_cards_is_enable', str(self.tpa_aquagliss_assignation_cards_enable))
        icp.set_param('tpa.aquagliss.card_method', self.tpa_aquagliss_name_method_card.strip())
        icp.set_param('tpa.aquagliss.card_technologies', self.tpa_aquagliss_technologies_card.strip())
        icp.set_param('tpa.aquagliss.card_categories', self.tpa_aquagliss_categories_card.strip())
        icp.set_param('tpa.aquagliss.area', self.tpa_aquagliss_area.id)

    @api.model
    def get_tpa_aquagliss_backend_url(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.aquagliss.backend_url', ''))

    @api.model
    def get_tpa_aquagliss_is_enable(self):
        return safe_eval(self.env['ir.config_parameter'].get_param('tpa.aquagliss.is_enable', 'False'))

    @api.model
    def get_tpa_aquagliss_partner_method(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.aquagliss.partner_method', ''))

    @api.model
    def get_tpa_aquagliss_cards_is_enable(self):
        return safe_eval(self.env['ir.config_parameter'].get_param('tpa.aquagliss.cards_is_enable', 'False'))

    @api.model
    def get_tpa_aquagliss_assignation_cards_enable(self):
        return safe_eval(self.env['ir.config_parameter'].get_param('tpa.aquagliss.assignation_cards_is_enable',
                                                                   'False'))

    @api.model
    def get_tpa_aquagliss_name_method_card(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.aquagliss.card_method', ''))

    @api.model
    def get_tpa_aquagliss_technologies_card(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.aquagliss.card_technologies', ''))

    @api.model
    def get_tpa_aquagliss_categories_card(self):
        return str(self.env['ir.config_parameter'].get_param('tpa.aquagliss.card_categories', ''))

    @api.model
    def get_tpa_aquagliss_area(self):
        return int(self.env['ir.config_parameter'].get_param('tpa.aquagliss.area', 0))

    # endregion

    pass
