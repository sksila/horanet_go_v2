from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MediumType(models.Model):
    """Type of medium, could be smart card or qr code."""

    # region Private attributes
    _name = 'partner.contact.identification.medium.type'
    _sql_constraints = [
        (
            'unicity_on_name',
            'UNIQUE(name)',
            _("A medium type with this name already exists.")
        )
    ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True, translate=True)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.multi
    @api.constrains('name')
    def _check_name(self):
        """Check if the name is valid.

        :raise: odoo.exceptions.ValidationError if the name is empty
        """
        for rec in self:
            if len(rec.name.strip()) == 0:
                raise ValidationError(_("Name cannot be empty"))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
