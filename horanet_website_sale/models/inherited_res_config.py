# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """Override ResConfigSettings class.

    Add terms_checkbox_checked field to define default status of terms checkbox in payment of cart view.
    Add shop_privacy_mode field to define if shop is private and can be accessed by authenticated users.
    Add hide_taxes_and_subtotal field to define if subtotal and tax are visible if tax is null.
    """

    # region Private attributes
    _inherit = 'res.config.settings'

    terms_checkbox_checked = fields.Boolean("Terms checkbox checked")
    shop_privacy_mode = fields.Selection(
        string="Shop privacy mode",
        selection=[
            ('public', "Public"),
            ('semi_private', "Semi private"),
            ('private', "Private")
        ],
        help="Public : Allow access to the shop to anonymous user \n"
             "Semi private : Allow access to the shop to anonymous user but redirect to login page when see product "
             "details \n Private : Redirect to login page when anonymous user try to access to the shop"
    )
    skip_checkout_addresses = fields.Boolean(
        string="Skip addresses checkout",
        help="Skip addresses checkout for frontend user in cart payment workflow.",
    )
    hide_taxes_and_subtotal = fields.Boolean("Hide taxes and subtotal", help="This option allow to hide taxes and "
                                                                             "subtotal from shop if the tax is null")

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
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('horanet_website_sale.terms_checkbox_checked', str(self.terms_checkbox_checked))
        self.env['ir.config_parameter'].sudo().set_param('horanet_website_sale.shop_privacy_mode', str(self.shop_privacy_mode))
        self.env['ir.config_parameter'].sudo().set_param('horanet_website_sale.skip_checkout_addresses', str(self.skip_checkout_addresses))
        self.env['ir.config_parameter'].sudo().set_param('horanet_website_sale.hide_taxes_and_subtotal', str(self.hide_taxes_and_subtotal))

    # region Model methods
    @api.model
    def get_terms_checkbox_checked(self):
        """Get the terms checkbox checked boolean.

        :return: Boolean terms_checkbox_checked setting
        """
        icp = self.env['ir.config_parameter'].sudo()
        return safe_eval(icp.get_param('horanet_website_sale.terms_checkbox_checked', 'False'))

    @api.model
    def get_shop_privacy_mode(self):
        """Get the terms checkbox checked boolean.

        :return: Boolean terms_checkbox_checked setting
        """
        icp = self.env['ir.config_parameter'].sudo()
        return icp.get_param('horanet_website_sale.shop_privacy_mode', 'public')

    @api.multi
    def set_shop_privacy_mode(self):
        """Set the terms checkbox checked boolean."""
        self.ensure_one()

        icp = self.env['ir.config_parameter']
        icp.set_param('horanet_website_sale.shop_privacy_mode', str(self.shop_privacy_mode))

    @api.model
    def get_skip_checkout_addresses(self):
        """Get the skip checkout addresses checked boolean.

        :return: Boolean skip_checkout_addresses setting
        """
        icp = self.env['ir.config_parameter'].sudo()
        return safe_eval(icp.get_param('horanet_website_sale.skip_checkout_addresses', 'False'))

    @api.model
    def get_hide_taxes_and_subtotal(self):
        """Get the terms checkbox checked boolean.

        :return: Boolean terms_checkbox_checked setting
        """
        icp = self.env['ir.config_parameter'].sudo()
        return safe_eval(icp.get_param('horanet_website_sale.hide_taxes_and_subtotal', 'False'))

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            terms_checkbox_checked=self.get_terms_checkbox_checked(),
            shop_privacy_mode=self.get_shop_privacy_mode(),
            skip_checkout_addresses=self.get_skip_checkout_addresses(),
            hide_taxes_and_subtotal=self.get_hide_taxes_and_subtotal(),
        )
        return res

    # endregion
    pass
