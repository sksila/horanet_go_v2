from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Technology(models.Model):
    """Represents the technology used by the manufacturer of a smart card."""

    # region Private attributes
    _name = 'partner.contact.identification.technology'
    _sql_constraints = [
        (
            'unicity_on_name',
            'UNIQUE(name)',
            _("A technology with this name already exists.")
        ),
        (
            'unicity_on_code',
            'UNIQUE(code)',
            _("A technology with this code already exists.")
        )
    ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)

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
