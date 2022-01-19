# coding: utf-8

from odoo import fields, models


class DepositArea(models.Model):
    # region Private attributes
    _name = 'environment.deposit.area'
    _inherits = {'horanet.infrastructure': 'infrastructure_id'}

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    infrastructure_id = fields.Many2one(string="Infrastructure",
                                        comodel_name='horanet.infrastructure',
                                        required=True, ondelete='cascade')

    deposit_point_ids = fields.One2many(string="Deposit points",
                                        comodel_name='environment.deposit.point',
                                        inverse_name='deposit_area_id',
                                        readonly=True)

    image = fields.Binary(string="Image")
    # endregion

    # region Fields method
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
