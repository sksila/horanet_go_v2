# coding: utf-8
from odoo.osv import expression
from odoo import fields

try:
    from odoo.addons.environment_waste_collect.controllers import device_ecopad_service
except ImportError:
    from environment_waste_collect.controllers import device_ecopad_service


class InheritDeviceWasteController(device_ecopad_service.DeviceWasteController):

    @staticmethod
    def get_environment_tags(odoo_environment, last_sync_date=None):
        """Overwrite method get_environment_tags to search for tag referencing partner AND move.

        By default this method only return tag referencing partner

        :param odoo_environment: An odoo environment
        :param last_sync_date: limit the search to the assignations write_date > last_sync_date
        :return: list of dict({
            'id': Int
            'active': Boolean
            'number': String
            'external_reference': String
            'write_date': String
            'partner_id': Int
            'is_guardian': Boolean
        """
        partner_tag_list = super(InheritDeviceWasteController, InheritDeviceWasteController).get_environment_tags(
            odoo_environment, last_sync_date)

        assignation_model = odoo_environment['partner.contact.identification.assignation']

        search_domain = []
        if last_sync_date:
            search_domain = expression.OR([
                [('write_date', '>', fields.Datetime.to_string(last_sync_date))],
                # Rechercher aussi les assignations qui ne seraient plus actives depuis la dernière synchro
                expression.AND([
                    assignation_model.search_is_active(operator='=', value=True, search_date=last_sync_date),
                    assignation_model.search_is_active(operator='=', value=False, search_date=fields.Datetime.now())
                ]),
                # Rechercher aussi les assignations qui ne seraient devenues actives depuis la dernière synchro
                expression.AND([
                    assignation_model.search_is_active(operator='=', value=False, search_date=last_sync_date),
                    assignation_model.search_is_active(operator='=', value=True, search_date=fields.Datetime.now())
                ])
            ])

        search_domain.extend([
            '&',
            ('reference_id', '!=', False),
            ('move_id', '!=', False)
        ])

        assignations = assignation_model.search(search_domain)

        list_tag_move = [{
            'id': assignation.tag_id.id,
            'active': assignation.tag_id.active and assignation.is_active,
            'number': assignation.tag_id.number,
            'external_reference': assignation.tag_id.external_reference,
            'write_date': assignation.write_date,
            'partner_id': assignation.move_id.partner_id.id,
            'is_guardian': False
        } for assignation in assignations]

        return list_tag_move + partner_tag_list
