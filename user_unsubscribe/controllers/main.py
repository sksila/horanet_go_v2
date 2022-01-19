# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError


class WebsiteUnsubscribe(http.Controller):
    @http.route(['/unsubscribe'], type='http', auth='user', website=True)
    def unsubscribe_user(self):
        """
        We redirect the user to the unsubcription page.

        We create the unsubscription request.
        """
        unsubscribe_request_count = request.env['user.unsubscribe'].search_count(
            [('user_id', '=', request.env.user.id)])
        if unsubscribe_request_count:
            return request.render('user_unsubscribe.user_unsubscribe_accepted')
        if request.httprequest.method == 'POST':
            user = request.env.user
            context = {}
            errors = []

            try:
                # We create the new request
                request.env['user.unsubscribe'].create({'user_id': user.id})
            except ValidationError as exs:
                # If errors, we redirect to the previous page.
                request.env.cr.rollback()
                for ex in exs.name.split('\n'):
                    errors.append(ex)
                context.update({'errors': errors})
                return request.render('user_unsubscribe.user_unsubscribe_page', context)
            return request.render('user_unsubscribe.user_unsubscribe_accepted')
        else:
            return request.render('user_unsubscribe.user_unsubscribe_page')
