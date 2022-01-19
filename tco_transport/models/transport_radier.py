# -*- coding: utf-8 -*-

from odoo import fields, models


class HoranetTransportRadier(models.Model):
    """A radier is a construction built above a river to prevents water flood.

    :term: `radier`
    """

    # region Private attributes
    _name = 'tco.transport.radier'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)
    city_id = fields.Many2one(string='City', comodel_name='res.city')
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
