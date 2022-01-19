# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.tools import safe_eval


class HoranetDematOrmcConfig(models.TransientModel):
    """Add new configuration fields on collectivity general config."""

    # region Private attributes
    _inherit = 'collectivity.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    required_nat_jur = fields.Boolean(string="Required NatJur for company")
    nat_jur_help = fields.Char(string="help message for nat jur")

    required_cat_tiers = fields.Boolean(string="Required CatTiers for company")
    cat_tiers_help = fields.Char(string="help message for cat tiers")

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def get_default_required_front_field(self, _):
        """Get default values of configuration fields."""
        return {
            'required_nat_jur': self.get_required_nat_jur(),
            'required_cat_tiers': self.get_required_cat_tiers(),
            'nat_jur_help': self.get_nat_jur_help(),
            'cat_tiers_help': self.get_cat_tiers_help(),
        }

    @api.model
    def set_required_front_field_default(self):
        """Set values of configuration fields."""
        icp = self.env['ir.config_parameter']
        icp.set_param('horanet_demat_ormc_psv2.required_nat_jur', str(self.required_nat_jur))
        icp.set_param('horanet_demat_ormc_psv2.required_cat_tiers', str(self.required_cat_tiers))
        icp.set_param('horanet_demat_ormc_psv2.nat_jur_help', str(self.nat_jur_help) if self.nat_jur_help else '')
        icp.set_param('horanet_demat_ormc_psv2.cat_tiers_help', str(self.cat_tiers_help) if self.cat_tiers_help else '')

    @api.model
    def get_required_nat_jur(self):
        """Get the configuration of required_nat_jur."""
        icp = self.env['ir.config_parameter']
        return safe_eval(icp.get_param('horanet_demat_ormc_psv2.required_nat_jur', 'False'))

    @api.model
    def get_required_cat_tiers(self):
        """Get the configuration of required_cat_tiers."""
        icp = self.env['ir.config_parameter']
        return safe_eval(icp.get_param('horanet_demat_ormc_psv2.required_cat_tiers', 'False'))

    @api.model
    def get_nat_jur_help(self):
        """Get the configuration of nat_jur_help."""
        icp = self.env['ir.config_parameter']
        return icp.get_param('horanet_demat_ormc_psv2.nat_jur_help', '')

    @api.model
    def get_cat_tiers_help(self):
        """Get the configuration of nat_jur_help."""
        icp = self.env['ir.config_parameter']
        return icp.get_param('horanet_demat_ormc_psv2.cat_tiers_help', '')

    # endregion
