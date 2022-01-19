import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Add firstname2 and lastname2 on partner."""

    # region Private attributes
    _name = 'res.partner'
    _inherit = ['res.partner', 'tools.field.dirty']
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    lastname2 = fields.Char(string="Second last name")
    firstname2 = fields.Char(string="Second first name")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.onchange('firstname')
    def _onchange_firstname(self):
        """Set the first letter of each word in titlecase."""
        if self.firstname:
            # Use .split(None) to match all words and trim whitespace in the string
            self.firstname = ' '.join(self.firstname.split(None)).title()

    @api.onchange('lastname')
    def _onchange_lastname(self):
        """Set the first letter of each word in uppercase."""
        if self.lastname:
            # Use .split(None) to match all words and trim whitespace in the string
            self.lastname = ' '.join(self.lastname.split(None)).upper()

    # endregion

    # region CRUD (overrides)
    @api.multi
    def write(self, vals):
        """Override write to correct values, before being stored."""
        for rec in self:
            rec._format_values(vals)

        return super(ResPartner, self).write(vals)

    @api.model
    def create(self, vals):
        """Override create method to correct values, before being stored."""
        self._format_values(vals)
        return super(ResPartner, self).create(vals)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def _format_values(self, vals):
        if vals.get('firstname', False):
            vals['firstname'] = ' '.join(vals['firstname'].split(None)).title()
        if vals.get('lastname', False):
            vals['lastname'] = ' '.join(vals['lastname'].split(None)).upper()

    # endregion

    pass
