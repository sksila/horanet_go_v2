# -*- coding: utf-8 -*-

import odoo.addons.website_portal.controllers.main as main

from odoo import fields, http
from odoo.http import request


class PartnerContactIdentificationWebsitePortal(main.website_account):
    @http.route()
    def account(self, **kw):
        """Send mediums number to account portal."""
        response = super(PartnerContactIdentificationWebsitePortal, self).account(**kw)

        medium_model = request.env['partner.contact.identification.medium']
        mediums_domain = self.get_domain_for_mediums()
        medium_count = medium_model.search_count(mediums_domain)

        response.qcontext.update({
            'medium_count': medium_count,
        })

        return response

    @http.route(['/my/mediums', '/my/mediums/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_mediums(self, page=1, **kw):
        """Show user's mediums in account portal."""
        values = self._prepare_portal_layout_values()

        medium_model = request.env['partner.contact.identification.medium']
        domain = self.get_domain_for_mediums()

        pager = request.website.pager(
            url="/my/mediums",
            total=medium_model.search_count(domain),
            page=page,
            step=self._items_per_page
        )

        mediums = medium_model.search(domain, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'mediums': mediums,
            'pager': pager,
            'default_url': '/my/mediums',
        })
        return request.render("partner_contact_identification.portal_my_mediums", values)

    @staticmethod
    def get_domain_for_mediums(domain=None):
        """Create domain for mediums.

        :param domain: dictionary to map
        :return: domain completed
        """
        if not domain:
            domain = list()
        partner = request.env.user.partner_id
        domain += [
            '&',
            '&',
            ('tag_ids.assignation_ids.reference_id', '=', 'res.partner,%d' % partner.id),
            ('is_lost', '=', False),
            '|',
            ('tag_ids.assignation_ids.end_date', '>=', fields.Datetime.now()),
            ('tag_ids.assignation_ids.end_date', '=', False),
        ]
        return domain

    pass
