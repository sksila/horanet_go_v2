# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PartnerMoveInheritedAssignation(models.Model):
    """Add possibility to reference packages."""

    # region Private attributes
    _inherit = 'partner.contact.identification.assignation'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    reference_id = fields.Reference(
        selection_add=[('partner.move', "Move")],
    )
    move_id = fields.Many2one(
        string="Move",
        comodel_name='partner.move',
        compute='_compute_move_id',
        store=True
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.depends('reference_id')
    def _compute_move_id(self):
        for assignation in self:
            if assignation.reference_id and assignation.reference_id._name == 'partner.move':
                assignation.move_id = assignation.reference_id
            else:
                assignation.move_id = False

    # endregion

    # region CRUD (overrides)
    @api.depends('move_id')
    def compute_display_name_assignation(self):
        u"""Calcul le nom des assignations liée a un emménagement (move).

        Une assignation peut être liée à plusieurs objets via un champ reference.
        Pour des raisons de performance, le nom de l'assignation est calculé à partir de l'objet référencé et non
        depuis le champ référence.

        Plusieurs méthodes surchargent le calcul du nom de l'assignation, chacune traitant un type d'objet.
        """
        move_assignation = self.filtered('move_id')
        for assignation in move_assignation:
            if assignation.move_id:
                assignation.display_name_assignation = assignation.move_id.name
        return super(PartnerMoveInheritedAssignation, self - move_assignation).compute_display_name_assignation()

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_partner_linked_to_assignation(self):
        """Return if it exists, the partner linked to the assignation via the move.

        doesn't matter if the assignation is linked to a move, a package or a partner.
        This method can be override to give the partner if the assignation point to a object other than a partner.

        :return: None or a partner (record)
        """
        move_assignations = self.filtered('move_id')

        linked_partner = super(
            PartnerMoveInheritedAssignation, self - move_assignations).get_partner_linked_to_assignation()

        for move_assignation in move_assignations:
            linked_partner += move_assignation.move_id.partner_id

        # Trick to remove duplicates
        linked_partner = linked_partner & linked_partner

        return linked_partner

    @api.multi
    def get_partner_linked_to_multiple_assignation(self):
        """Return if it exists, the partner linked to the assignation via the package.

        doesn't matter if the assignation is linked to a move, a package or a partner.
        This method can be override to give the partner if the assignation point to a object other than a partner.

        :return: dictionary <tag:(assignation_start_date, assignation_end_date, partner)>
        """
        package_assignations = self.filtered('move_id')

        result = super(
            PartnerMoveInheritedAssignation, self - package_assignations).get_partner_linked_to_multiple_assignation()

        for ass in package_assignations:
            result[ass.tag_id].append((ass.start_date, ass.end_date, ass.move_id.partner_id))

        return result
    # endregion

    pass
