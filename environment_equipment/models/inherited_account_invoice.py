# -*- coding: utf-8 -*-

from odoo import models


class InheritedAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_dict_equipments_usages(self):
        """Get a dictionnary containing a dictionnary of usages informations for each equipment."""
        equipment_list = []
        list_usages = self.get_usages_from_invoice()

        equipments = list_usages.mapped('origin_operation_id.maintenance_equipment_id')

        if list_usages:
            for equ in equipments:
                equipment_dict = {}
                usages = list_usages.mapped('origin_operation_id')\
                    .filtered(lambda r: r.maintenance_equipment_id == equ).mapped('resulting_usage_ids')
                equipment_dict['id'] = equ.id
                equipment_dict['chip_number'] = equ.chip_number
                equipment_dict['category_id'] = equ.category_id.name
                equipment_dict['usage_quantity'] = len(usages)
                equipment_dict['usages'] = usages

                equipment_list.append(equipment_dict)

        return equipment_list
