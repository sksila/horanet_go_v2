# -*- coding: utf-8 -*-

from odoo.addons.portal.controllers.portal import CustomerPortal as website_account
from odoo import http
from odoo.http import request


class MyEquipmentPortalWebsiteAccount(website_account):
    @http.route()
    def account(self, **kw):
        """Add the number of waste sites deposits."""
        response = super(MyEquipmentPortalWebsiteAccount, self).account(**kw)

        deposit_count = request.env['horanet.operation'] \
            .search_count([('activity_id.application_type', '=', 'environment'),
                           ('action_id', '=',
                            request.env.ref('environment_waste_collect.horanet_action_depot').id),
                           '|',
                           ('partner_id', '=', request.env.user.partner_id.id),
                           ('operation_partner_id', '=', request.env.user.partner_id.id)
                           ])

        access_count = request.env['horanet.operation'] \
            .search_count([('action_id', '=',
                            request.env.ref('horanet_subscription.action_access').id),
                           '|',
                           ('partner_id', '=', request.env.user.partner_id.id),
                           ('operation_partner_id', '=', request.env.user.partner_id.id)
                           ])

        response.qcontext.update({
            'waste_site_deposit_count': deposit_count,
            'waste_site_access_count': access_count,
        })
        return response

    @http.route(['/my/waste-site-deposits'], type='http', auth='user', website=True)
    def my_waste_site_deposits(self, date_begin=None, date_end=None):
        """Get all the waste sites deposits.

        We use the archive groups.
        """
        values = self._prepare_portal_layout_values()

        domain = [('activity_id.application_type', '=', 'environment'),
                  ('action_id', '=',
                   request.env.ref('environment_waste_collect.horanet_action_depot').id),
                  '|',
                  ('partner_id', '=', request.env.user.partner_id.id),
                  ('operation_partner_id', '=', request.env.user.partner_id.id)]

        archive_groups = self._get_archive_groups('horanet.operation', domain)

        if date_begin and date_end:
            domain += [('time', '>=', date_begin), ('time', '<', date_end)]

        deposits = request.env['horanet.operation'].sudo().search(domain)

        values.update({
            'deposits': deposits,
            'archive_groups': archive_groups,
            'date': date_begin,
            'total': len(deposits),
        })

        return request.render('environment_waste_collect.my_waste_site_deposits', values)

    @http.route(['/my/waste-site-access'], type='http', auth='user', website=True)
    def my_waste_site_access(self, date_begin=None, date_end=None):
        """Get all the waste sites access.

        We use the archive groups.
        """
        values = self._prepare_portal_layout_values()

        domain = [('action_id', '=', request.env.ref('horanet_subscription.action_access').id),
                  '|',
                  ('partner_id', '=', request.env.user.partner_id.id),
                  ('operation_partner_id', '=', request.env.user.partner_id.id)]

        archive_groups = self._get_archive_groups('horanet.operation', domain)

        if date_begin and date_end:
            domain += [('time', '>=', date_begin), ('time', '<', date_end)]

        accesses = request.env['horanet.operation'].sudo().search(domain)

        values.update({
            'accesses': accesses,
            'archive_groups': archive_groups,
            'date': date_begin,
            'total': len(accesses),
        })

        return request.render('environment_waste_collect.my_waste_site_access', values)
