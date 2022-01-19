
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ContainerType(models.Model):

    _name = 'environment.container.type'

    name = fields.Char(string="Name", required=True)
    volume = fields.Integer(string="Volume (m3)")

    @api.multi
    @api.constrains('name')
    def _check_name(self):
        """Check if name is valid.

        :raise: odoo.exceptions.ValidationError if the name is empty
        """
        for rec in self:
            if len(rec.name.strip()) == 0:
                raise ValidationError(_("Name cannot be empty"))
