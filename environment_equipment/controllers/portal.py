# -*- coding: utf-8 -*-

from odoo.addons.website_portal.controllers.main import website_account
from odoo import http
from odoo.http import request


class MyEquipmentPortalWebsiteAccount(website_account):
    @http.route()
    def account(self, **kw):
        """Add the number of pickups."""
        response = super(MyEquipmentPortalWebsiteAccount, self).account(**kw)

        pickup_count = request.env['horanet.operation'] \
            .search_count([('activity_id.application_type', '=', 'environment'),
                           ('action_id', '=',
                            request.env.ref('environment_equipment.horanet_action_container_pickup').id),
                           ('maintenance_equipment_id.owner_partner_id', '=', request.env.user.partner_id.id)
                           ])

        response.qcontext.update({
            'pickup_count': pickup_count,
        })
        return response

    @http.route(['/my/pickups'], type='http', auth='user', website=True)
    def my_pickups(self, date_begin=None, date_end=None):
        """Get all the pickups.

        We use the archive groups.
        """
        values = self._prepare_portal_layout_values()

        domain = [('activity_id.application_type', '=', 'environment'),
                  ('action_id', '=', request.env.ref('environment_equipment.horanet_action_container_pickup').id),
                  ('maintenance_equipment_id.owner_partner_id', '=', request.env.user.partner_id.id)]

        archive_groups = self._get_archive_groups('horanet.operation', domain)

        if date_begin and date_end:
            domain += [('time', '>=', date_begin), ('time', '<', date_end)]

        pickups = request.env['horanet.operation'].sudo().search(domain)

        values.update({
            'pickups': pickups,
            'archive_groups': archive_groups,
            'date': date_begin,
        })

        return request.render('environment_equipment.my_pickups', values)
