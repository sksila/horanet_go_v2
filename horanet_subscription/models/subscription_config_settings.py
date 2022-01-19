from odoo import models, fields, api


class SubscriptionSettings(models.TransientModel):
    """Modèle de paramétrage général de l'application subscription."""

    # region Private attributes
    _inherit = 'res.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    rule_exception_unknown_tag_message = fields.Char(
        string="Message if unknown tag",
        help="Message to respond to a query with an unknown tag")

    rule_exception_unknown_tag_response = fields.Selection(
        string="Response if unknown tag",
        selection=[('yes', 'Yes'), ('no', 'No')],
        help="Response value to a query with an unknown tag",
    )

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

    @api.multi
    def set_values(self):
        """Set values for the fields other that `default`, `group` and `module`."""
        super(SubscriptionSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        # we store the repr of the values, since the value of the parameter is a required string
        ICPSudo.set_param('subscription.unknown_tag_message', str(self.rule_exception_unknown_tag_message))
        # we store the repr of the values, since the value of the parameter is a required string
        ICPSudo.set_param(
            'subscription.unknown_tag_response',
            'yes' if self.rule_exception_unknown_tag_response == 'yes' else 'no'
        )

    @api.model
    def get_values(self):
        """Return values for the fields other that `default`, `group` and `module`."""
        res = super(SubscriptionSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        unknown_tag_message = str(ICPSudo.get_param('subscription.unknown_tag_message', default=''))
        unknown_tag_response = ICPSudo.get_param('subscription.unknown_tag_response', default='no')

        rule_exception_unknown_tag_response = 'no' if unknown_tag_response != 'yes' else 'yes'
        res.update(
            rule_exception_unknown_tag_message=unknown_tag_message,
            rule_exception_unknown_tag_response=rule_exception_unknown_tag_response,
        )
        return res

    @api.model
    def get_unknow_tag_route_response(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        unknown_tag_message = str(ICPSudo.get_param('subscription.unknown_tag_message', default=''))
        unknown_tag_response = ICPSudo.get_param('subscription.unknown_tag_response', default='no')
        return {
            'response': unknown_tag_response == 'yes',
            'message': unknown_tag_message,
        }
# endregion
