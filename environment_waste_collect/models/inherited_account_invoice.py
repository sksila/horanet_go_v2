# -*- coding: utf-8 -*-

from odoo import models


class InheritedAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_list_waste_collect_usages(self):
        """
        Get a list of equipment usages.

        :return: list of equipment usages
        """
        list_usages = self.get_usages_from_invoice()

        usages = list_usages.filtered(lambda u: u.origin_operation_id.infrastructure_id)

        return usages
