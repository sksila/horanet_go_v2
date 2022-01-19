# -*- coding: utf-8 -*-

import werkzeug

from odoo import _
from odoo.http import Controller, request, route


class TVCBController(Controller):
    def get_partner_titles(self):
        mister_title = request.env.ref('base.res_partner_title_mister')
        madam_title = request.env.ref('base.res_partner_title_madam')

        return [mister_title, madam_title]

    def check_crc(self, data):
        if not data:
            raise werkzeug.exceptions.Unauthorized()

        part1 = data[0:10]
        crc = int(data[10:12])
        part2 = data[12:]

        sum = 0
        for i in part1 + part2:
            sum += ord(i)

        sum &= 0xffff  # Force sum to be on two bytes
        low = sum & 0xff  # Get the last byte
        high = sum >> 8  # Get the first byte

        inverse_hex_sum = hex(low) + hex(high).replace('x', '')

        inverse_sum = int(inverse_hex_sum, 16)

        if crc != (inverse_sum % 100):
            raise werkzeug.exceptions.Unauthorized()

    @route('/tvcb/partner/create', type='http', auth='public', methods=['GET', 'POST'], website=True)
    def create_partner(self, par1=None, bulk_create=False, **kw):
        self.check_crc(par1)

        template_name = 'tvcb_website_create_partner.create_partner'
        context = {
            'bulk_create': bulk_create,
            'partner_titles': self.get_partner_titles(),
            'par1': par1,
            'creation_success': kw.get('creation_success'),
            'partner': kw.get('partner'),
            'create_user': True
        }

        if request.httprequest.method == 'POST':
            zip_model = request.env['res.zip'].sudo()
            zip_id = zip_model.search([('name', '=', kw.get('zipcode'))]).id

            street = self.get_or_create_street(
                kw.get('street_id'), kw.get('street'), kw.get('city_id')
            )

            if kw.get('street_number_id'):
                street_number_id = kw.get('street_number_id')
            else:
                street_number_id = self.get_or_create_street_number(kw.get('street_number'))

            state_id = street.city_id.country_state_id.id
            country_id = street.city_id.country_state_id.country_id.id

            existing_partner = None
            if kw.get('email'):
                existing_partner = request.env['res.users'].sudo().search([
                    ('login', '=', kw.get('email'))
                ]).partner_id

            if kw.get('create_user') and existing_partner:
                email_message_error = _(
                   'This email belongs to %s which address is %s. '
                   'Click on "Save" to add %s %s in the family of %s.'
                ) % (existing_partner.name, existing_partner.better_contact_address,
                     kw.get('name'), kw.get('firstname'), existing_partner.name)

                context.update(kw)
                context.update({
                    'email_error': email_message_error,
                    'city': street.city_id.name,
                    'create_user': False
                })
                return request.render(template_name, context)

            citizen_partner = request.env.ref(
                'horanet_auth_signup.horanet_template_customer_res_partner'
            ).sudo()
            partner = citizen_partner.create({
                'title': int(kw.get('title_id')),
                'lastname': kw.get('name').upper(),
                'firstname': kw.get('firstname').title(),
                'street_number_id': street_number_id,
                'street_id': street.id,
                'street2': kw.get('additional_address'),
                'zip_id': zip_id,
                'city_id': int(kw.get('city_id')),
                'state_id': state_id,
                'country_id': country_id,
                'email': kw.get('email'),
                'phone': kw.get('phone_number'),
                'tpa_membership_aquagliss': True,
                'lang': citizen_partner.lang,
                'tz': citizen_partner.tz
            })

            if not existing_partner and kw.get('create_user'):
                citizen_user = request.env.ref('horanet_auth_signup.horanet_template_customer').sudo()
                citizen_user.copy({
                    'login': partner.email,
                    'partner_id': partner.id,
                    'active': True,
                    'lang': citizen_user.lang
                })
            elif existing_partner:
                if not existing_partner.foyer_relation_ids:
                    existing_partner.action_add_foyer()

                family_relation_model = request.env['horanet.relation.foyer'].sudo()
                family_relation_model.create({
                    'foyer_id': existing_partner.foyer_relation_ids[0].foyer_id.id,
                    'partner_id': partner.id
                })

            request.env.ref('horanet_tpa_aquagliss.scheduler_synchronization_aquagliss') \
                       .sudo() \
                       .method_direct_trigger()

            return request.redirect(u'{}?par1={}&creation_success=True&partner={}'.format(
                request.httprequest.path, context.get('par1'), partner.name
            ))

        return request.render(template_name, context)

    def get_or_create_street_number(self, number):
        street_number_model = request.env['res.street.number'].sudo()

        street_number = street_number_model.search([('name', '=', number)])

        if street_number:
            return street_number.id

        return street_number_model.create({'name': number}).id

    def get_or_create_street(self, street_id, street_name, city_id):
        street_model = request.env['res.street'].sudo()

        if street_id:
            return street_model.browse(int(street_id))
        else:
            street = street_model.search([
                ('name', '=', street_name.upper()),
                ('city_id', '=', int(city_id))
            ])

            if street:
                return street[0]
            else:
                return street_model.create({
                    'name': street_name.upper(),
                    'city_id': int(city_id)
                })
