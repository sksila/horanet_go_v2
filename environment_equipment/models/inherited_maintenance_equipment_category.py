# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools


class InheritedEquipmentCategory(models.Model):

    # region Private attributes
    _inherit = 'maintenance.equipment.category'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    capacity = fields.Integer(sring="Capacity")
    capacity_unit_id = fields.Many2one(string="Capacity unit", comodel_name='product.uom')
    activity_id = fields.Many2one(
        string="Activity",
        comodel_name='horanet.activity',
        domain="[('default_action_id.code', '=', 'RELEVEBAC')]"
    )
    image = fields.Binary(string="Image")
    use_product = fields.Boolean(string="Use product")
    product_id = fields.Many2one(string="Product", comodel_name='product.template')
    active = fields.Boolean(default=True)

    equipment_follows_producer = fields.Boolean(string="Equipment follows producer")
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        if 'image' in vals:
            vals.update({
                'image': tools.image_resize_image(
                    base64_source=vals['image'],
                    size=(96, 96),
                    encoding='base64',
                    avoid_if_small=True
                )
            })

        return super(InheritedEquipmentCategory, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'image' in vals:
            vals.update({
                'image': tools.image_resize_image(
                    base64_source=vals['image'],
                    size=(96, 96),
                    encoding='base64',
                    avoid_if_small=True
                )
            })

        return super(InheritedEquipmentCategory, self).write(vals)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
