
from odoo import fields, models


class Activity(models.Model):
    _inherit = 'horanet.activity'

    smarteco_product_id = fields.Integer(string="SmartEco Product ID")
