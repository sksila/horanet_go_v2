import logging
from odoo import models, fields, api, _

logger = logging.getLogger(__name__)


class StreetNumber(models.Model):
    """This model represent a street number (address)."""

    # region Private attributes
    _name = 'res.street.number'
    _order = "name asc"
    _sql_constraints = [
        ('unicity_on_number', 'UNIQUE(name)', _('The street number must be unique'))]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Number', required=True)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to search street number that 'start with'."""
        logger.info("Entering name_search() of HoranetStreetNumber")
        if args is None:
            args = []
        res = []
        ids = self.search([('name', '=ilike', str(name) + '%')] + args, limit=limit).ids
        for rec in self.browse(ids):
            res.append((rec.id, str(rec.display_name)))
        return res

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
