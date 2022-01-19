# -*- coding: utf-8 -*-

from odoo import models


class InheritedAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_dict_tags_usages(self):
        """Get a dictionnary containing a dictionnary of usages informations for each tag."""
        tag_list = []
        list_usages = self.get_usages_from_invoice()

        tags = list_usages.mapped('origin_operation_id.tag_id')

        if list_usages:
            for tag in tags:
                tag_dict = {}
                usages = list_usages.mapped('origin_operation_id')\
                    .filtered(lambda r: r.tag_id == tag).mapped('resulting_usage_ids')
                tag_dict['chip_number'] = tag.number
                tag_dict['usage_quantity'] = len(usages)
                tag_dict['usages'] = usages

                tag_list.append(tag_dict)

        return tag_list
