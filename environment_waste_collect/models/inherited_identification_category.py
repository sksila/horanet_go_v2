
import re

from odoo import models, api


class IdentificationCategory(models.Model):
    _inherit = 'res.partner.id_category'

    @api.multi
    def validate_id_number(self, id_number):
        super(IdentificationCategory, self.with_context({'re': re})).validate_id_number(id_number)
