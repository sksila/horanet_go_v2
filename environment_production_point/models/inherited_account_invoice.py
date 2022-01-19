# -*- coding: utf-8 -*-

from odoo import models


class InheritedAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_production_point(self):
        if self.subscription_id:
            return self.env['partner.move'].search([
                ('subscription_id', '=', self.subscription_id.id),
            ], order='start_date DESC', limit=1).production_point_id
        else:
            return self.env['production.point']
