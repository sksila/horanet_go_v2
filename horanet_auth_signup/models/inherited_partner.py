import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SignupError(Exception):
    """Class of Exception to handle exceptions."""

    pass


class ResPartner(models.Model):
    """Surcharge du modèle partner pour modifier la gestion du login.

    - Ajoute une action de création de compte automatique.
    """

    # region Private attributes
    _inherit = 'res.partner'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    has_default_portal_group = fields.Boolean(
        string="Has default portal group",
        compute='_compute_has_default_portal_group',
        store=False,
    )

    # endregion

    # region Fields method
    @api.multi
    @api.depends()
    def _compute_has_default_portal_group(self):
        portal_group = self.env['res.config.settings'].get_access_portal_group_default()
        for rec in self:
            has_default_portal_group = False
            if rec.user_ids:
                has_default_portal_group = portal_group in rec.user_ids[0].groups_id
            rec.has_default_portal_group = has_default_portal_group

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def signup_retrieve_info(self, token):
        """Retrieve the user info about the token.

        :return: a dictionary with the user information
        """
        result = super(ResPartner, self).signup_retrieve_info(token)
        partner = self._signup_retrieve_partner(token, raise_exception=True)
        if partner.firstname:
            result.update({'firstname': partner.firstname})
        if partner.lastname:
            result.update({'lastname': partner.lastname})
        return result

    @api.model
    def _signup_retrieve_partner(self, token, check_validity=False, raise_exception=False):
        """Override method to search inactive partner."""
        # On modifie la méthode pour pouvoir chercher sur un partner inactif
        partner_ids = self.with_context(active_test=False).search([('signup_token', '=', token)])
        if not partner_ids:
            if raise_exception:
                raise SignupError("Signup token '%s' is not valid" % token)
            return False
        partner = partner_ids[0]
        if check_validity and not partner.signup_valid:
            if raise_exception:
                raise SignupError("Signup token '%s' is no longer valid" % token)
            return False
        return partner

    # endregion

    # region Actions
    @api.multi
    def action_create_portal_access(self):
        self.ensure_one()
        portal_group = self.env['res.config.settings'].get_access_portal_group_default()
        if not portal_group.is_portal:
            portal_group.is_portal = True

        portal_wizard = self.env['portal.wizard'].create({'portal_id': portal_group.id})
        portal_wizard.user_ids = [(0, 0, {
            'partner_id': self.id,
            'email': self.email,
            'in_portal': True,
        })]
        portal_wizard.user_ids.action_apply()

    # endregion

    # region Model methods
    # endregion

    pass
