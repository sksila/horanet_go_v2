from odoo.addons.partner_contact_citizen.tools import check_phone_number

from odoo import api, models, fields, exceptions
from odoo.osv import expression
from odoo.tools import safe_eval


class AddInternationalPhoneOnPartner(models.Model):
    """Add interntational phone and mobile on partners."""

    # region Private attributes
    _inherit = 'res.partner'

    # endregion

    # region Default methods
    @api.model
    def _default_country_phone(self):
        # Le pays par défaut est celui sélectionné dans la configuration d'Odoo
        icp_model = self.env['ir.config_parameter'].sudo()
        default_country_id = safe_eval(icp_model.get_param('horanet_website_account.default_country_id', 'False'))
        return default_country_id or self.env.ref('base.fr').id

    # endregion

    # region Fields declaration
    country_phone = fields.Many2one(string="Country phone", comodel_name='res.country',
                                    default=_default_country_phone)
    country_phone_code = fields.Integer(string="Country phone code", related='country_phone.phone_code',
                                        readonly=True)
    national_prefix = fields.Text(string="National prefix", related='country_phone.national_prefix', readonly=True)
    display_international_phone = fields.Char(string="Display international phone",
                                              compute='_compute_international_phone',
                                              search='_search_international_phone')

    country_mobile = fields.Many2one(string="Country mobile", comodel_name='res.country',
                                     default=_default_country_phone)
    country_mobile_code = fields.Integer(string="Country mobile code", related='country_mobile.phone_code',
                                         readonly=True)
    display_international_mobile = fields.Char(string="Display international mobile",
                                               compute='_compute_international_mobile',
                                               search='_search_international_mobile')

    # endregion

    # region Fields method
    @api.depends('country_phone_code', 'national_prefix', 'phone')
    def _compute_international_phone(self):
        """
        Convert phone number into international phone number.

        International phone number format : '+' + 'country phone code' + 'phone number without national prefix'
        Exemple: for france, the country phone code is 33 and the national prefix is 0,
        So the number 0123456789 become +33123456789
        """
        for rec in self.filtered('phone'):
            phone_number = rec.phone.replace(" ", "").replace("-", "").replace(".", "").replace("/", "")
            rec.phone = phone_number

            # national_prefix+phone ex: 0123......
            if rec.national_prefix and phone_number[0:len(rec.national_prefix)] == rec.national_prefix:
                rec.display_international_phone = "+" + str(rec.country_phone_code) + \
                                                  phone_number[len(rec.national_prefix):]

            # country_phone_code+phone ex: 33123....
            elif rec.country_phone and phone_number[0:len(str(rec.country_phone_code))] == \
                    str(rec.country_phone_code):
                rec.display_international_phone = "+" + phone_number

            # +country_phone_code+phone ex:+33123....
            elif phone_number[0] == "+":
                rec.display_international_phone = phone_number

            # phone ex: 123....
            else:
                rec.display_international_phone = "+" + str(rec.country_phone_code) + phone_number

    @api.depends('country_mobile_code', 'mobile')
    def _compute_international_mobile(self):
        """
        Convert mobile number into international mobile number.

        International mobile number format : '+' + 'country phone code' + 'mobile number without 0'
        Exemple: for france, the country phone code is 33, so the number 0623456789 become +33623456789
        """
        for rec in self.filtered('mobile'):
            mobile_number = rec.mobile.replace(" ", "").replace("-", "").replace(".", "").replace("/", "")

            if mobile_number != "0":
                if mobile_number[0] == "0":
                    mobile_number = mobile_number[1:]

                # 33612.....
                if rec.country_mobile and mobile_number[0:len(str(rec.country_mobile_code))] == \
                        str(rec.country_mobile_code):
                    rec.display_international_mobile = "+" + mobile_number
                # +33612......
                elif mobile_number[0] == "+":
                    rec.display_international_mobile = mobile_number
                # 612.....
                else:
                    rec.display_international_mobile = "+" + str(rec.country_mobile_code) + mobile_number

    def _search_international_phone(self, operator, value):
        """
        Search partner by international phone.

        For the phone number 0123456789, if value is 0123456789 or +33123456789 the result is optimal
        but for value 123456789 or 33123456789 we ignore the first three digits because we can't know if the
        country phone code (here 33 for France) is present (the value can be 3333456789). The country phone code can
        have three digits so we ignore the three first digits.
        :param operator: search operator
        :param value: searched value
        :return: a domain that filters on the `phone` field
        """
        search_domain = []
        if isinstance(value, bool):
            search_domain = [('phone', '=', False)]

        else:
            value = value.replace(' ', '').replace('-', '').replace('.', '').replace('/', '')
            if value[0] == '+':
                if self.env['res.country'].search([('phone_code', '=', value[1:4])]):
                    search_domain = [('phone', 'like', value[4:])]
                elif self.env['res.country'].search([('phone_code', '=', value[1:3])]):
                    search_domain = [('phone', 'like', value[3:])]
                elif self.env['res.country'].search([('phone_code', '=', value[1])]):
                    search_domain = [('phone', 'like', value[2:])]

            # General case where the first digit is 0 (national prefix of France)
            elif value[0] == '0':
                search_domain = [('phone', 'like', value[1:])]

            else:
                search_domain = [('phone', 'like', value[3:])]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            search_domain = [expression.NOT_OPERATOR] + search_domain

        return search_domain

    def _search_international_mobile(self, operator, value):
        """
        Search partner by international mobile.

        For the mobile number 0123456789, if value is 0123456789 or +33123456789 the result is optimal
        but for value 123456789 or 33123456789 we ignore the first three digits because we can't know if the
        country mobile code (here 33 for France) is present (the value can be 3333456789).
        The country mobile code can have three digits.
        :param operator: search operator
        :param value: searched value
        :return: a domain that filters on the `mobile` field
        """
        search_domain = []
        if isinstance(value, bool):
            search_domain = [('mobile', '=', False)]

        else:
            value = value.replace(' ', '').replace('-', '').replace('.', '').replace('/', '')
            if value[0] == '+':
                if self.env['res.country'].search([('phone_code', '=', value[1:4])]):
                    search_domain = [('mobile', 'like', value[4:])]
                elif self.env['res.country'].search([('phone_code', '=', value[1:3])]):
                    search_domain = [('mobile', 'like', value[3:])]
                elif self.env['res.country'].search([('phone_code', '=', value[1])]):
                    search_domain = [('mobile', 'like', value[2:])]

            # General case where the first digit is 0 (national prefix of France)
            elif value[0] == '0':
                search_domain = [('mobile', 'like', value[1:])]

            else:
                search_domain = [('mobile', 'like', value[3:])]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            search_domain = [expression.NOT_OPERATOR] + search_domain

        return search_domain

    # endregion

    # region Constrains and Onchange
    @api.onchange('country_id')
    def _set_country_phone(self):
        if not self.country_phone_code:
            self.country_phone = self.country_id.id

    @api.constrains('phone', 'mobile', 'country_phone', 'country_mobile')
    def check_phone_number(self):
        """
        Check phone number and mobile number.

        Phone number format accepted: '0123456789' '123456789' '33123456789' '+33123456789' (for France)
        Mobile number format accepted: '0612345678' '612345678' '3312345678' '+3312345678'  (for France)
        """
        for rec in self:
            error = dict()
            error_message = []
            error_validation = dict()
            error_message_validation = []

            if rec.phone:
                error_validation, error_message_validation = \
                    check_phone_number.validation_phone_number(rec.phone, rec.country_phone_code,
                                                               rec.national_prefix, error, error_message)

            if rec.mobile:
                error_validation, error_message_validation = \
                    check_phone_number.validation_mobile_number(rec.mobile, rec.country_mobile_code,
                                                                rec.country_mobile.mobile_prefix, error, error_message)

            if error_validation:
                raise exceptions.ValidationError('\n'.join(error_message_validation))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
