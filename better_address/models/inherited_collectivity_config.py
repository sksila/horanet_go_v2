from odoo import models, fields, api
from odoo.tools import safe_eval
import logging

_logger = logging.getLogger(__name__)


class LocationSettings(models.TransientModel):
    """This class represent a the location settings."""

    # region Private attributes
    _inherit = 'res.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    protected_countries_ids = fields.Many2many(
        string='List of country with protected address',
        comodel_name='res.country',
        help="""A regular user will not be able to create a city or a country state belonging to the selected \
        countries (these record are supposed to have been imported)""")

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
    @api.model
    def get_values(self):
        """Get the list of protected countries.

        :return: id of protected countries
        """
        res = super(LocationSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        # we use safe_eval on the result, since the value of the parameter is a nonempty string
        protected_countries_ids = safe_eval(ICPSudo.get_param('collectivity.config_protected_countries', 'False'))
        res.update(protected_countries_ids=protected_countries_ids)
        return res

    @api.multi
    def set_values(self):
        """Store the id of protected country."""
        super(LocationSettings, self).set_values()
        config = self
        if config.protected_countries_ids != self.get_protected_countries_ids():
            # if the protected_countries has changed, a recompute will be triggered to recompute
            # res.partner.address_state field
            ICPSudo = self.env['ir.config_parameter'].sudo()
            ICPSudo.set_param(
                'collectivity.config_protected_countries',
                str(config.protected_countries_ids.mapped('id'))
            )
            _logger.info('Recomputing address status on res.partner')
            res_partner_model = self.env['res.partner']
            self.env.add_todo(res_partner_model._fields['address_status'], res_partner_model.search([]))
            res_partner_model.recompute()

    @api.model
    def get_protected_countries_ids(self):
        """Get the country list to set to be protected.

        :return: record set of res.country
        """
        icp = self.env['ir.config_parameter']
        list_country_ids = safe_eval(icp.get_param('collectivity.config_protected_countries', 'False'))
        return self.env['res.country'].browse(list_country_ids)

    # endregion

    pass
