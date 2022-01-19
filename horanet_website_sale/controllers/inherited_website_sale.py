# -*- coding: utf-8 -*-

import logging

import odoo.addons.website_sale.controllers.main as main
import werkzeug.utils

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebsiteSaleExtension(main.WebsiteSale):
    """Override WebsiteSale controller from website_sale module."""

    @http.route()
    def payment(self, **post):
        """Override payment route to add value 'checkbox_checked' to know if terms are checked by default or not."""
        res = super(WebsiteSaleExtension, self).payment(**post)
        checkbox_checked = request.env['res.config.settings'].get_terms_checkbox_checked()
        res.qcontext.update({
            'checkbox_checked': checkbox_checked
        })
        return res

    @http.route()
    def address(self, **kw):
        """Override address route to set values for address formulary as defined in horanet_website_account."""
        if request.httprequest.method == 'POST':
            # As we don't ask the state we need to find it by the city
            if kw.get('city_id'):
                kw['state_id'] = request.env['res.city'].sudo().browse(int(kw['city_id'])).country_state_id.id

            # And the zip is used to retrieve the city but we don't have its ID
            if kw.get('zipcode'):
                kw['zip_id'] = request.env['res.zip'].sudo().search([('name', '=', kw['zipcode'])], limit=1).id

            if kw.get('create_new_street') and kw.get('new_street'):
                street_model = request.env['res.street'].sudo()
                search = street_model.search([('name', '=', kw['new_street']),
                                              ('city_id.id', '=', int(kw['city_id']))], limit=1)
                if not search:
                    new_street = street_model.create(
                        {'name': kw['new_street'], 'city_id': int(kw['city_id'])})
                    kw['street_id'] = new_street.id
                else:
                    kw['street_id'] = search.id

        res = super(WebsiteSaleExtension, self).address(**kw)

        user = request.env.user

        # Le partner est soit celui fourni, ou le "public user" si l'utilisateur n'est pas enregistré
        partner = kw.get('partner_id', False) and request.env['res.partner'] \
            .browse(int(kw.get('partner_id'))) or user.partner_id

        res.qcontext.update({
            'user': user,  # Utilisateur courant
            'partner': partner,
            'mode_creation': not bool(user.partner_id),
            'partner_titles': request.env['res.partner.title'].search([]),
            'post': kw,  # Data du PostBack pour conservation de saisi
        })

        return res

    def _get_mandatory_billing_fields(self):
        """Override mandatory billing fields to have the same required fields as better_address module require."""
        return ['name', 'email', 'country_id', 'state_id', 'city_id', 'zip_id', 'street_number_id', 'street_id']

    def _get_mandatory_shipping_fields(self):
        """Override mandatory shipping fields to have the same required fields as better_address module require."""
        return ['name', 'country_id', 'state_id', 'city_id', 'zip_id', 'street_number_id', 'street_id']

    def values_postprocess(self, order, mode, values, errors, error_msg):
        """Override values_postprocess to process address values from horanet_website_account formulary."""
        new_values, errors, error_msg = super(WebsiteSaleExtension, self).values_postprocess(order, mode, values,
                                                                                             errors, error_msg)

        new_values['city_id'] = values.get('city_id')
        new_values['zip_id'] = values.get('zip_id')
        new_values['street_number_id'] = values.get('street_number_id')
        new_values['street_id'] = values.get('street_id')
        new_values['street2'] = values.get('street2')

        return new_values, errors, error_msg

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        """Make shop accessible for authenticated users only if shop is private."""
        shop_is_private = http.request.env['res.config.settings'].get_shop_is_private()
        if shop_is_private and not http.request.session.uid:
            url = '/' + http.request.httprequest.url.replace(http.request.httprequest.host_url, '')
            return werkzeug.utils.redirect('/web/login?redirect=' + url, 303)

        return super(WebsiteSaleExtension, self).shop(page, category, search, ppg, **post)

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        """Make products accessible for authenticated users only if shop is private."""
        shop_is_private = http.request.env['res.config.settings'].get_shop_is_private()
        if shop_is_private and not http.request.session.uid:
            url = '/' + http.request.httprequest.url.replace(http.request.httprequest.host_url, '')
            return werkzeug.utils.redirect('/web/login?redirect=' + url, 303)

        return super(WebsiteSaleExtension, self).product(product, category='', search='', **kwargs)

    @http.route()
    def checkout(self, **post):
        res = super(WebsiteSaleExtension, self).checkout(**post)

        if res.status_code != 200:
            return res

        skip_checkout_addresses = http.request.env['res.config.settings'].get_skip_checkout_addresses()
        if skip_checkout_addresses:
            return werkzeug.utils.redirect('/shop/payment')

        return res
