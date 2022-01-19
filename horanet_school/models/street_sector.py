# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HoranetStreetSector(models.Model):
    # region Private attributes
    _name = 'res.street.sector'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    street_id = fields.Many2one(string='Street', comodel_name='res.street', required=True)
    name = fields.Char(related="street_id.name", readonly=True)
    street_code = fields.Char(related='street_id.code', readonly=True)
    city_id = fields.Many2one(related='street_id.city_id', readonly=True)

    odd_start = fields.Integer(string='Odd street number start', default=1)
    odd_end = fields.Integer(string='Odd street number end', default=False)
    even_start = fields.Integer(string='Even street number start', default=2)
    even_end = fields.Integer(string='Even street number end', default=False)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('odd_start', 'odd_end')
    def _check_odd_values(self):
        """Constrain on odds.

        :return: ValidationError if odd beginning number > odd ending number
        """
        for rec in self:
            if rec.odd_start and rec.odd_end and rec.odd_start > rec.odd_end:
                raise ValidationError(_("Odd beginning number must be inferior to odd ending number"))

    @api.constrains('even_start', 'even_end')
    def _check_even_values(self):
        """Constrain on even.

        :return: ValidationError
        """
        for rec in self:
            if rec.even_start and rec.even_end and rec.even_start > rec.even_end:
                raise ValidationError(_("Even beginning number must be inferior to even ending number"))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
