# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of odoo
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class HoranetTransportStationType(models.Model):
    # region Private attributes
    _name = 'tco.transport.station.type'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('name')
    def _check_name(self):
        """Check if the name is valid.

        :raise: odoo.exceptions.ValidationError if the field is empty
        """
        for rec in self:
            if len(rec.name.strip()) == 0:
                raise exceptions.ValidationError(_('Name cannot be empty'))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
