# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class TCOInscription(models.Model):
    """Class of TCO inscription period."""

    # region Private attributes
    _name = 'tco.inscription.period'
    _sql_constraints = [('unicity', 'UNIQUE(name)', _('A period with the same name already exist'))]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name")
    active = fields.Boolean(string="Is active", default=True)
    date_start = fields.Date(string="Date start")
    date_end = fields.Date(string="Date end")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('date_start', 'date_end')
    def _check_date(self):
        """To check if the dates are valid."""
        for rec in self:
            if rec.date_end and rec.date_start and rec.date_start > rec.date_end:
                raise exceptions.ValidationError(_("Beginning date must be inferior to ending date"))
            domain = [('id', '!=', rec.id)]
            if rec.date_start:
                domain.extend([('date_end', '>=', rec.date_start)])
            if rec.date_end:
                domain.extend([('date_start', '<=', rec.date_end)])
            duplicate = self.search(domain, limit=1)
            if duplicate:
                raise exceptions.ValidationError(_("The period dates overlap with period {name}").format(
                    name=duplicate.name))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
