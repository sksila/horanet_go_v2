# -*- coding: utf-8 -*-

from odoo.addons.website_portal.controllers.main import website_account
from odoo import http
from odoo.http import request


class MyEquipmentPortalWebsiteAccount(website_account):
    @http.route()
    def account(self, **kw):
        """Add the number of pickups."""
        response = super(MyEquipmentPortalWebsiteAccount, self).account(**kw)

        deposit_count = request.env['horanet.operation'] \
            .search_count([('activity_id.application_type', '=', 'environment'),
                           ('action_id', '=',
                            request.env.ref('environment_deposit_point.horanet_action_depot_pav').id),
                           '|',
                           ('partner_id', '=', request.env.user.partner_id.id),
                           ('operation_partner_id', '=', request.env.user.partner_id.id)
                           ])

        response.qcontext.update({
            'deposit_count': deposit_count,
        })
        return response

    @http.route(['/my/pav-deposits'], type='http', auth='user', website=True)
    def my_pav_deposits(self, date_begin=None, date_end=None):
        """Get all the deposits from deposits points.

        We use the archive groups.
        """
        values = self._prepare_portal_layout_values()

        domain = [('activity_id.application_type', '=', 'environment'),
                  ('action_id', '=',
                   request.env.ref('environment_deposit_point.horanet_action_depot_pav').id),
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

        return request.render('environment_deposit_point.my_pav_deposits', values)
