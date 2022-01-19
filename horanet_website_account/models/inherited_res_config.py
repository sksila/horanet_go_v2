# coding: utf-8

from odoo import fields, models, api
from odoo.tools import safe_eval


class BaseConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _get_default_front_office(self):
        custom_view = self.env['ir.ui.view'].search([('name', '=', 'inherit partner informations for customization')],
                                                    limit=1)

        if custom_view and custom_view.active is True:
            return custom_view
        else:
            return self.env['ir.ui.view'].search([('name', '=', 'inherit partner informations for customization'),
                                                  ('active', '=', False)], limit=1)

    manage_employees = fields.Boolean(string="Allow professionals to manage their employees",
                                      help="Professionals will have access to the My Company tab and will manage "
                                           "their employees.")

    required_vat_number = fields.Boolean(string="Required vat number")

    required_siret_code = fields.Boolean(string="Required siret code")

    required_ape_code = fields.Boolean(string="Required ape code")

    custom_front_view_id = fields.Many2one(string="Custom front view",
                                           comodel_name='ir.ui.view',
                                           default=_get_default_front_office,
                                           readonly=True,
                                           store=False)

    country_id = fields.Many2one(
        string="Default country used for portal users",
        comodel_name='res.country',
        help=('Used to set the default country value on website '
              '"My personal informations" page')
    )

    @api.model
    def get_values(self):
        """Return values for the fields other that `default`, `group` and `module`."""
        res = super(BaseConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        manage_employees = safe_eval(ICPSudo.get_param('horanet_website_account.manage_employees', 'False'))
        required_vat_number = safe_eval(ICPSudo.get_param('horanet_website_account.required_vat_number', 'False'))
        required_siret_code = safe_eval(ICPSudo.get_param('horanet_website_account.required_siret_code', 'False'))
        required_ape_code = safe_eval(ICPSudo.get_param('horanet_website_account.required_ape_code', 'False'))
        country_id = safe_eval(ICPSudo.get_param('horanet_website_account.default_country_id', 'False'))
        if not country_id:
            country_id = self.env.ref('base.fr').id

        res.update(
            manage_employees=manage_employees,
            required_vat_number=required_vat_number,
            required_siret_code=required_siret_code,
            required_ape_code=required_ape_code,
            country_id=country_id,
        )
        return res

    @api.multi
    def set_values(self):
        """Set values for the fields other that `default`, `group` and `module`."""
        super(BaseConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('horanet_website_account.manage_employees', str(self.manage_employees))
        ICPSudo.set_param('horanet_website_account.required_vat_number', str(self.required_vat_number))
        ICPSudo.set_param('horanet_website_account.required_siret_code', str(self.required_siret_code))
        ICPSudo.set_param('horanet_website_account.required_ape_code', str(self.required_ape_code))
        ICPSudo.set_param('horanet_website_account.default_country_id', self.country_id.id)
