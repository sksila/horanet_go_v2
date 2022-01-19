from odoo import fields, models, api


class InheritedAssignation(models.Model):
    """Add possibility to reference packages."""

    # region Private attributes
    _inherit = 'partner.contact.identification.assignation'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    reference_id = fields.Reference(selection_add=[('horanet.package', "Package")])

    package_id = fields.Many2one(
        string="Package",
        comodel_name='horanet.package',
        compute='_compute_package_id',
        store=True,
    )

    # endregion

    # region Fields method
    @api.depends('reference_id')
    def _compute_package_id(self):
        for rec in self:
            if rec.reference_id and rec.reference_id._name == 'horanet.package':
                rec.package_id = rec.reference_id
            else:
                rec.package_id = False

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.depends('package_id')
    def compute_display_name_assignation(self):
        u"""Calcul le nom des assignations liée a une ligne de contrat (horanet.package).

        Une assignation peut être liée à plusieurs objets via un champ reference.
        Pour des raisons de performance, le nom de l'assignation est calculé à partir de l'objet référencé et non
        depuis le champ référence.

        Plusieurs méthodes surchargent le calcul du nom de l'assignation, chacune traitant un type d'objet.
        """
        packages_assignations = self.filtered('package_id')
        for assignation in packages_assignations:
            if assignation.package_id:
                assignation.display_name_assignation = assignation.package_id.name
        return super(InheritedAssignation, self - packages_assignations).compute_display_name_assignation()

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_partner_linked_to_assignation(self):
        u"""Return if it exists, the partner linked to the assignation via the package.

        doesn't matter if the assignation is linked to a move, a package or a partner.
        This method can be override to give the partner if the assignation point to a object other than a partner.

        :return: None or a partner (record)
        """
        package_assignations = self.filtered('package_id')

        linked_partner = super(
            InheritedAssignation, self - package_assignations).get_partner_linked_to_assignation()

        for package_assignation in package_assignations:
            linked_partner += package_assignation.package_id.recipient_id

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
        package_assignations = self.filtered('package_id')

        result = super(
            InheritedAssignation, self - package_assignations).get_partner_linked_to_multiple_assignation()

        for ass in package_assignations:
            result[ass.tag_id].append((ass.start_date, ass.end_date, ass.package_id.recipient_id))

        return result
    # endregion

    pass
