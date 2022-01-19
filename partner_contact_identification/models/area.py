from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Area(models.Model):
    """An area is the perimeter of the mapping.

    It could be for example: transport or cultural and should represents
    the activity domain of the mapping it would be linked
    """

    # region Private attributes
    _name = 'partner.contact.identification.area'
    _sql_constraints = [
        (
            'unicity_on_name',
            'UNIQUE(name)',
            _("An area with this name already exists.")
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
        """Check if name is valid.

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
