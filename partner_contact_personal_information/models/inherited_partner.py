import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models, exceptions
from odoo.osv import expression
from ..config import config

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    gender = fields.Selection(
        string='Gender',
        selection=config.PARTNER_GENDER,
        groups='partner_contact_personal_information.group_contact_information_gender')

    birthdate_date = fields.Date(
        string="Birthdate",
        copy=False,
        groups='partner_contact_personal_information.group_contact_information_birth_date')
    partner_age = fields.Float(
        string='Age',
        compute='_compute_partner_age',
        store=False,
        search='_search_partner_age',
        groups='partner_contact_personal_information.group_contact_information_birth_date')
    display_partner_age = fields.Char(
        string='Age',
        compute='_compute_display_partner_age',
        store=False,
        groups='partner_contact_personal_information.group_contact_information_birth_date')

    quotient_fam = fields.Integer(
        string='Family quotient',
        default=0,
        copy=True,
        groups='partner_contact_personal_information.group_contact_information_quotient_fam')

    birth_country_id = fields.Many2one(
        string='Country of birth',
        comodel_name='res.country',
        copy=False,
        help="Select the country of birth",
       )
    birth_state_id = fields.Many2one(
        string='State of birth',
        comodel_name='res.country.state',
        domain="[('country_id', '=?', birth_country_id)]",
        copy=False,
        help="Select the state of birth",
        groups='partner_contact_personal_information.group_contact_information_birth_place')
    birth_city_id = fields.Char(
        string='City of birth',
        copy=False,
        help="Select the city of birth",
        groups='partner_contact_personal_information.group_contact_information_birth_place')

    # endregion

    # region Fields method
    @api.multi
    @api.depends('birthdate_date')
    @api.onchange('birthdate_date')
    def _compute_partner_age(self):
        """Compute age of a partner corresponding to its birthdate.

        The age is store on a float like : years.month
        example : 24 years and 8 months will render like : 24.08
        """
        # Vérification du droit d'accès à la date de naissance avant de calculer l'âge. Normalement les champs
        # display_age et birthdate_date sont liée par le même groupe, mais des exceptions peuvent survenir.
        try:
            self.check_field_access_rights('read', ['birthdate_date'])
        except exceptions.AccessError:
            return

        today = fields.Date.from_string(fields.Date.context_today(self))
        for rec in self:
            if rec.birthdate_date:
                birth = fields.Date.from_string(rec.birthdate_date)
                nb_years = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                nb_months = 0
                if today.day >= birth.day:
                    if today.month >= birth.month:
                        nb_months = today.month - birth.month
                    else:
                        nb_months = 12 - (birth.month - today.month)
                else:
                    if today.month > birth.month:
                        nb_months = (today.month - birth.month) - 1
                    else:
                        nb_months = 11 - (birth.month - today.month)

                rec.partner_age = nb_years + (nb_months / 100.)

    @api.multi
    @api.depends('partner_age')
    def _compute_display_partner_age(self):
        """Compute the age displayed of the partner."""
        for rec in self:
            if rec.partner_age:
                nb_year = int(rec.partner_age)
                nb_month = int(float(str((rec.partner_age % 1) * 100)))
                tmp = _("{nb_year} {year_txt}").format(
                    nb_year=nb_year,
                    year_txt=_("Years") if nb_year > 1 else _("Year"))
                if nb_month > 0:
                    tmp += _(" and {nb_month} {month_txt}").format(
                        nb_month=nb_month,
                        month_txt=_("months") if nb_month > 1 else _("month"))

                rec.display_partner_age = tmp

    def _search_partner_age(self, operator, value):
        """Search on partner age.

        Field partner_age is a non stored computed field that depends on birthdate_date.
        Field birthdate_date isn't always filled.
        """
        domain = expression.FALSE_DOMAIN

        if operator in ['=', '!=', '<', '<=', '>', '>=']:
            domain = [('birthdate_date', '!=', False)]
            if value and isinstance(value, int):
                date_threshold = datetime.now() - relativedelta(years=value)
            elif value and isinstance(value, str) and value.isdigit():
                date_threshold = datetime.now() - relativedelta(years=int(value))

            if date_threshold:
                domain.append(('birthdate_date', '<=', fields.Datetime.to_string(date_threshold)))
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = [expression.NOT_OPERATOR] + domain

        return expression.normalize_domain(domain)

    # endregion

    # region Constrains and Onchange
    @api.onchange('title')
    def _onchange_title(self):
        """Update the partner gender corresponding to selected title."""
        for rec in self:
            if rec.title:
                rec.gender = rec.title.gender

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
