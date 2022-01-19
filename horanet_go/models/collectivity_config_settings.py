from odoo import models, fields, api


class CollectivitySettings(models.TransientModel):
    """Modèle de paramétrage général des modules horanet collectivité."""

    # region Private attributes
    _inherit = 'res.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    module_partner_contact_personal_information = fields.Boolean(
        string="Use personal information",
        help="Install the module partner_contact_personal_information which add new personal field on partner")

    module_partner_merge = fields.Boolean(
        string="Merge partners to avoid duplicate",
        help="Install the module partner_merge which allow merge of partners",
    )

    use_sequence_partner_internal_ref = fields.Boolean(
        string="Use sequence for the partner internal reference",
        help="This sequence is used when a partner is create",
    )

    unicity_on_partner_internal_ref = fields.Boolean(
        string="Apply a unicity on the field internal reference on partner",
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
    @api.model
    def get_values(self):
        """Return values for the fields other that `default`, `group` and `module`."""
        res = super(CollectivitySettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        use_sequence_partner_internal_ref = ICPSudo.get_param(
            'horanet_go.use_sequence_partner_internal_ref',
            default=False
        )
        unicity_on_partner_internal_ref = ICPSudo.get_param(
            'horanet_go.unicity_on_partner_internal_ref',
            default=False
        )
        res.update(
            use_sequence_partner_internal_ref=use_sequence_partner_internal_ref,
            unicity_on_partner_internal_ref=unicity_on_partner_internal_ref,
        )
        return res

    @api.multi
    def set_values(self):
        """Set values for the fields other that `default`, `group` and `module`."""
        super(CollectivitySettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('horanet_go.use_sequence_partner_internal_ref', self.use_sequence_partner_internal_ref)
        ICPSudo.set_param('horanet_go.allow_uninvited', self.unicity_on_partner_internal_ref)

    # endregion
    pass
