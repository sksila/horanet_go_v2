from odoo import models, fields, api, _
from odoo.tools import safe_eval

KEY_PARAM_SIGNUP_COMPANY = 'horanet_auth_signup.auth_signup_allow_title_company'
KEY_PARAM_SIGNUP_PERSON = 'horanet_auth_signup.auth_signup_allow_title_person'
KEY_PARAM_INVALID_SIGNUP_HOURS = 'horanet_auth_signup.invalid_signup_limit_hours'


class BaseConfigSettings(models.TransientModel):
    """Add signup configurations."""

    # region Private attributes
    _inherit = 'base.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    auth_signup_allow_title_person = fields.Boolean(
        string="Allow individuals to signup on portal",
        help="The user could signup as a person, and could choose it's title and lastname/firstname"
             "(for exemple Mr. Smith)",
    )
    auth_signup_allow_title_company = fields.Boolean(
        string="Allow legal entities to signup on portal",
        help="The user could signup as a company, and could choose it's title and company name"
             "(for exemple ETS. AwesomeCompany)",
    )

    invalid_signup_limit_hours = fields.Char(
        string="Delete user who didn't finish his signup after ",
        help="Invalid signup: when a user didn't set his password. by default 360h (15 days)"
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.onchange('auth_signup_allow_title_person', 'auth_signup_allow_title_company')
    def _onchange_auth_signup_allow_title(self):
        """Return alert to informe user of potentials mistakes."""
        title_model = self.env['res.partner.title']
        if self.auth_signup_uninvited:
            if not (self.auth_signup_allow_title_person or self.auth_signup_allow_title_company):
                return {
                    'warning': {
                        'title': _("Warning!"),
                        'message': _("Allowing external users to sign up required at least "
                                     "one of the following options:\n"
                                     " - Allow individuals to signup on portal\n"
                                     " - Allow legal entities to signup on portal\n"
                                     "If neither, no one could signup!"),
                    }
                }
            elif self.auth_signup_allow_title_person and not title_model.search([('is_company_title', '=', False)]):
                return {
                    'warning': {
                        'title': _("Warning!"),
                        'message': _("Allowing legal entities to signup on portal option is active,"
                                     " but no company titles found on the system.")
                    }
                }
            elif self.auth_signup_allow_title_company and not title_model.search([('is_company_title', '=', True)]):
                return {
                    'warning': {
                        'title': _("Warning!"),
                        'message': _("Allowing individuals to signup on portal option is active,"
                                     " but no person titles found on the system.")
                    }
                }
        return {}

    @api.onchange('invalid_signup_limit_hours')
    def _onchange_invalid_signup_hours(self):
        """Return alert to informe user of potentials mistakes."""
        try:
            int(self.invalid_signup_limit_hours)
        except ValueError:
            return {
                'warning': {
                    'title': _("Warning!"),
                    'message': _("Time (hours) to complete a signup must be integer."),
                }
            }
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def get_auth_signup_allow_title_person(self):
        u"""Get the parameter 'allow personal title on signup form' boolean value."""
        icp_model = self.env['ir.config_parameter']
        return safe_eval(icp_model.get_param(KEY_PARAM_SIGNUP_PERSON, 'True'))

    @api.model
    def get_auth_signup_allow_title_company(self):
        u"""Get the parameter 'allow company title on signup form' boolean value."""
        icp_model = self.env['ir.config_parameter']
        return safe_eval(icp_model.get_param(KEY_PARAM_SIGNUP_COMPANY, 'True'))

    @api.model
    def get_invalid_signup_limit_hours(self):
        u"""Get the parameter 'invalid_signup_limit_hours' Char value. By default 360 hours (=15days)."""
        icp_model = self.env['ir.config_parameter']
        return icp_model.get_param(KEY_PARAM_INVALID_SIGNUP_HOURS, '360')

    @api.model
    def get_values(self):
        """Return values for the fields other that `default`, `group` and `module`."""
        res = super(BaseConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        auth_signup_pro = ICPSudo.get_param('auth_signup.auth_signup_pro', default=False)
        auth_signup_collectivities = ICPSudo.get_param('auth_signup.auth_signup_collectivities', default=False)
        auth_signup_associations = ICPSudo.get_param('auth_signup.auth_signup_associations', default=False)
        auth_signup_individual = ICPSudo.get_param('auth_signup.allow_signup_individual', default=False)

        auth_signup_legal_entities = False
        if auth_signup_pro or auth_signup_collectivities or auth_signup_associations:
            auth_signup_legal_entities = True

        res.update(
            auth_signup_individual=auth_signup_individual,
            auth_signup_legal_entities=auth_signup_legal_entities,
            auth_signup_pro=auth_signup_pro,
            auth_signup_collectivities=auth_signup_collectivities,
            auth_signup_associations=auth_signup_associations
        )
        return res

    @api.multi
    def set_values(self):
        """Set values for the fields other that `default`, `group` and `module`."""
        super(BaseConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('auth_signup.allow_signup_individual', self.auth_signup_individual)

        ICPSudo.set_param('auth_signup.auth_signup_pro', self.auth_signup_pro)
        ICPSudo.set_param('auth_signup.auth_signup_collectivities', self.auth_signup_collectivities)
        ICPSudo.set_param('auth_signup.auth_signup_associations', self.auth_signup_associations)

    # endregion

    pass
