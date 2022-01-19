
from odoo import models, fields, api


class CollectivityContactSettings(models.TransientModel):
    """Add new configuration fields on collectivity general config."""

    # region Private attributes
    _inherit = 'res.config.settings'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    param_group_contact_merge = fields.Selection(
        string="Merge contacts",
        selection=[(0, "Only for users in 'Merge contacts' group"),
                   (1, "For users in 'Contact creation' group")],
        help="Only for users in 'Merge contacts' group or Only for users in 'Contact creation' group"
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
    def get_default_param_group_contact_merge(self, _):
        u"""Recherche si le droit de fusion est est attribué au droits de création de contact."""
        return {
            'param_group_contact_merge': 1 if self._is_group_contact_merge_in_group_partner_manager() else 0
        }

    @api.model
    def set_param_group_contact_merge(self):
        u"""Modifie les attribut du group base.group_partner_manager en fonction du paramétrage de la configuration.

        Si 'Contact creation' est sélectionné, alors, ajouter le groupe de droit de fusion dans le groupe de
        création de contact (base.group_partner_manager)

        :return: nothing
        """
        # test si la valeur du paramètre à changé, pour ne pas modifier inutilement les groupes
        is_implied_with_contact_creation = self._is_group_contact_merge_in_group_partner_manager()
        if bool(self.param_group_contact_merge) != is_implied_with_contact_creation:
            self.env.ref('base.group_partner_manager').write({
                'implied_ids': [(4 if bool(self.param_group_contact_merge) else 3,
                                 self._get_group_contact_merge().id)]
            })

    def _is_group_contact_merge_in_group_partner_manager(self):
        u"""Détermine si le droit de fusionner les contact est donné par le droit de création de contact.

        :return: True or False
        """
        employee_group = self.env.ref('base.group_user')
        perso_info_group = self._get_group_contact_personal_information()
        return perso_info_group in employee_group.implied_ids

    def _get_group_contact_merge(self):
        u"""Recherche du record correspondant au groupe de droit de merge de contact.

        :return: res.group record
        """
        return self.env.ref('partner_merge.group_contact_merge')

    # endregion
