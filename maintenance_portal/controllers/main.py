# -*- coding: utf-8 -*-

from odoo.addons.website_portal.controllers.main import website_account
from odoo import http
from odoo.http import request


class MaintenancePortalWebsiteAccount(website_account):
    @http.route()
    def account(self, **kw):
        """Add the number of maintenance request."""
        response = super(MaintenancePortalWebsiteAccount, self).account(**kw)

        maintenance_count = request.env['maintenance.request'].search_count([])

        response.qcontext.update({
            'maintenance_count': maintenance_count,
        })
        return response

    @http.route(['/my/maintenance'], type='http', auth='user', website=True)
    def my_maintenance_requests(self):
        """Get all the maintenance requests."""
        values = self._prepare_portal_layout_values()
        maintenance_requests = request.env['maintenance.request'].search([])

        values.update({
            'maintenance_requests': maintenance_requests,
        })

        return request.render('maintenance_portal.my_maintenance_requests', values)
