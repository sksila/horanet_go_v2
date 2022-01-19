import logging

from odoo import models, fields, api
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class AuthSignupSettings(models.TransientModel):
    """This class represent a the location settings."""

    # region Private attributes
    _inherit = 'res.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    access_portal_group_default = fields.Many2one(
        string="Quick access portal group",
        comodel_name='res.groups',
        help="The group used to give a user a portal access, if the user isn't in this group, a button on the partner "
             "form will be visible in order to add the group to the partner",
        domain="[('is_portal','=',True)]")

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
    def get_values(self):
        """Return values for the fields other that `default`, `group` and `module`."""
        res = super(AuthSignupSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        # we use safe_eval on the result, since the value of the parameter is a nonempty string
        access_portal_group_default = safe_eval(ICPSudo.get_param('auth.access_portal_group_default', default='False'))
        res.update(access_portal_group_default=access_portal_group_default)
        return res

    @api.multi
    def set_values(self):
        """Set values for the fields other that `default`, `group` and `module`."""
        super(AuthSignupSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('auth.access_portal_group_default', str(self.access_portal_group_default.id))

    @api.model
    def get_access_portal_group_default(self):
        u"""Get the parameter 'access_portal_group_default' value (record res.groups id)."""
        icp = self.env['ir.config_parameter']
        # Use safe_eval on the result, since the value of the parameter is a nonempty string
        group_id = safe_eval(icp.get_param('auth.access_portal_group_default', 'False'))
        return self.env['res.groups'].browse(group_id)

    # endregion

    pass
