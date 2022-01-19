# coding: utf-8

from odoo import models, fields


class EquipmentStatus(models.Model):
    _name = 'equipment.status'

    name = fields.Char()
    code = fields.Char()
