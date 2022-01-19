# -*- coding: utf-8 -*-

from odoo.addons.website_application.controllers.main import WebsitePortalApplications

from odoo import http
from odoo.http import request


class TCOWebsitePortalApplications(WebsitePortalApplications):
    @http.route()
    def account(self, **kw):
        """Add requests to main account page and a counter."""
        response = super(TCOWebsitePortalApplications, self).account(**kw)
        user = request.env.user

        inscriptions = request.env['tco.inscription.transport.scolaire']

        inscription_count = inscriptions.search_count([('responsible_id', '=', user.partner_id.id)])

        request_count = response.qcontext.get('request_count', 0) + inscription_count

        response.qcontext.update({
            'request_count': request_count,
        })
        return response

    @http.route(['/my/requests'], type='http', auth='user', method=['GET'], website=True)
    def get_requests(self, date_begin=None, date_end=None):
        """Construct a website page used to display all the inscriptions related to the user."""
        response = super(TCOWebsitePortalApplications, self).get_requests(date_begin, date_end)
        user = request.env.user

        domain = [('responsible_id', '=', user.partner_id.id)]

        # On va utiliser les archives_groups et fusionner celles des inscriptions avec celles des téléservices
        archive_groups = self._get_archive_groups('tco.inscription.transport.scolaire', domain)
        list1 = {k['date_end']: k.copy() for k in response.qcontext['archive_groups']}
        for archive in archive_groups:
            if list1.get(archive['date_end'], False):
                archive['item_count'] += list1[archive['date_end']]['item_count']
            else:
                archive.update({archive['date_end']: archive})

        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<', date_end)]

        inscriptions = request.env['tco.inscription.transport.scolaire'].sudo().search(domain)

        response.qcontext.update({
            'user': user,
            'inscriptions': inscriptions,
            'archive_groups': archive_groups,
            'date': date_begin,
        })
        return response
