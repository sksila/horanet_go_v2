from odoo import models, fields, api


class CollectivityContactSettings(models.TransientModel):
    """Add new configuration fields on collectivity general config."""

    # region Private attributes
    _inherit = 'res.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    group_contact_personal_information = fields.Selection(
        string="Personal information page",
        selection=[(0, "Visible only for users in group 'Contact personal information'"),
                   (1, "Visible for everyone")]
    )
    group_add_personal_gender = fields.Boolean(
        string="Use gender",
        group='partner_contact_personal_information.group_contact_personal_information',
        implied_group="partner_contact_personal_information.group_contact_information_gender",
    )
    group_add_personal_birth_date = fields.Boolean(
        string="Use birthdate/age",
        group='partner_contact_personal_information.group_contact_personal_information',
        implied_group="partner_contact_personal_information.group_contact_information_birth_date",
    )
    group_add_personal_birth_place = fields.Boolean(
        string="Use birth place",
        group='partner_contact_personal_information.group_contact_personal_information',
        implied_group="partner_contact_personal_information.group_contact_information_birth_place",
    )
    group_add_personal_family_quotient = fields.Boolean(
        string="Use family quotient",
        group='partner_contact_personal_information.group_contact_personal_information',
        implied_group="partner_contact_personal_information.group_contact_information_quotient_fam",
    )

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
    def get_values(self):
        """Return values for the fields other that `default`, `group` and `module`."""
        res = super(CollectivityContactSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        group_add_personal_family_quotient = ICPSudo.get_param(
            'partner_contact_personal_information.group_add_personal_family_quotient', default=False)

        # Recherche si oui ou non le groupe d'information personnelle est attribué à tout les users.
        # Afin de valuer la valeur du paramétrage d'affectation du groupe d'information personnelle
        group_contact_personal_information = 1 if self._is_group_personal_information_for_everyone() else 0
        res.update(
            group_add_personal_family_quotient=group_add_personal_family_quotient,
            group_contact_personal_information=group_contact_personal_information
        )
        return res

    @api.multi
    def set_values(self):
        """Set values for the fields other that `default`, `group` and `module`."""
        super(CollectivityContactSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            'partner_contact_personal_information.group_add_personal_family_quotient',
            self.group_add_personal_family_quotient
        )
        # Modifie les attributs du group base.users en fonction du paramétrage de la configuration.
        # Si 'for everyone' est sélectionné, alors,
        #  ajouter le groupe d'information personnelle dans le groupe des employés (base.users) aka : tout le monde
        # test si la valeur du paramètre à changé, pour ne pas modifier inutilement les groupes
        is_for_everyone = self._is_group_personal_information_for_everyone()
        if bool(self.group_contact_personal_information) != is_for_everyone:
            self.env.ref('base.group_user').write({
                'implied_ids': [(4 if bool(self.group_contact_personal_information) else 3,
                                 self._get_group_contact_personal_information().id)]
            })

    def _is_group_personal_information_for_everyone(self):
        """Détermine si le groupe d'information personnelle est dans le groupe base.users.

        :return: True or False
        """
        employee_group = self.env.ref('base.group_user')
        perso_info_group = self._get_group_contact_personal_information()
        return perso_info_group in employee_group.implied_ids

    def _get_group_contact_personal_information(self):
        """Recherche du record correspondant au groupe d'information personnelle de contact.

        :return: res.group record
        """
        return self.env.ref('partner_contact_personal_information.group_contact_personal_information')

    # endregion
