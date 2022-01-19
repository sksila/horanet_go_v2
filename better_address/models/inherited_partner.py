import logging

from odoo import models, fields, api, _
from ..config import config

_logger = logging.getLogger(__name__)

# new address fields copy if 'use_parent_address' is checked
BETTER_ADDRESS_FIELDS = ['street_id', 'street_number_id', 'street2', 'zip_id', 'city_id']
EXCLUDE_ADDRESS_FIELDS = ['street', 'street2', 'zip', 'city']


class ResPartner(models.Model):
    """Add the new address fields on res.partner."""

    # region Private attributes
    _name = 'res.partner'
    _inherit = ['res.partner', 'tools.field.dirty']

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # Add the new address fields
    city_id = fields.Many2one(
        string='City',
        comodel_name='res.city',
        help="select the city",
        domain="[('country_state_id', '=?', state_id), ('zip_ids.name', '=?', zip)]")
    street_id = fields.Many2one(
        string='Street',
        comodel_name='res.street',
        domain="[('city_id', '=?', city_id)]")
    zip_id = fields.Many2one(
        string='ZIP code',
        comodel_name='res.zip',
        domain="[('city_ids', '=?', city_id)]")
    street_number_id = fields.Many2one(
        string='N°',
        comodel_name='res.street.number')
    street3 = fields.Char(
        string='Second additional address')
    address_status = fields.Selection(
        string='Address State',
        selection=config.PARTNER_ADDRESS_STATUS,
        track_visibility='onchange',
        compute='get_address_status',
        store=True,
        help=_("Address state:\n"
               " * Normal is the default situation\n"
               " * Invalid indicates the selected value are not 'referential'"))

    # binding of the original fields with the new ones
    city = fields.Char(compute='_compute_city', store=True)
    zip = fields.Char(compute='_compute_zip', store=True)
    street = fields.Char(compute='_compute_street', store=True)

    better_contact_address = fields.Char(
        string='Better complete Address',
        compute='_compute_better_contact_address',
        search='_search_better_contact_address',
        store=False)

    # endregion

    # region Fields method
    @api.model
    def _search_better_contact_address(self, operator, value):
        """Search method to search partner by address.

        this method as two distinct process for the search query:

            - if the value is a word (no space) the search is performed in each field address
            independently of the other
            - if the value is a sentence, the search is performed on an concatenated string in SQL
            this string is build the same way that the method :meth:`~._compute_better_contact_address`
            to let the user perform a search on the same address-string displayed in the view

        :return: a domain
        """
        if not isinstance(value, str):
            return []

        search_name = '%%%s%%' % value
        res_domain = []
        if ' ' not in value:
            res_domain = ['|', '|', '|', '|', '|', '|',
                          ('street', operator, search_name),
                          ('street2', operator, search_name),
                          ('street3', operator, search_name),
                          ('zip', operator, search_name),
                          ('city', operator, search_name),
                          ('country_id.name', operator, search_name),
                          ('state_id.name', operator, search_name), ]
        else:
            cr = self.env.cr
            query = """SELECT ADDRESS.ID AS PARTNER_ID
                        FROM
                            (SELECT TRIM(REGEXP_REPLACE(
                                COALESCE(STREET, '')|| ' '||
                                COALESCE(STREET2, '') || ' ' ||
                                COALESCE(STREET3, '') || ' ' ||
                                COALESCE(CITY, '') || ' ' ||
                                COALESCE(ZIP, '')  || ' ' ||
                                COALESCE(S.NAME, '') || ' ' ||
                                COALESCE(C.NAME, ''),
                                 '\s+', ' ', 'g'))
                                AS FULL_ADDRESS,P.ID
                            FROM RES_PARTNER AS P
                                LEFT JOIN RES_COUNTRY_STATE S ON P.STATE_ID = S.ID
                                LEFT JOIN RES_COUNTRY C ON P.COUNTRY_ID = C.ID) AS ADDRESS
                        WHERE ADDRESS.FULL_ADDRESS {operator} {percent}""".format(
                operator=operator,
                percent='%s')
            cr.execute(query, [search_name])
            ids = list(set([x[0] for x in cr.fetchall()]))
            res_domain = [('id', 'in', ids)]

        return res_domain

    @api.multi
    @api.depends('city_id.name', )
    def _compute_city(self):
        for partner in self:
            partner.city = partner.city_id and partner.city_id.name or ''

    @api.multi
    @api.depends('zip_id.name', )
    def _compute_zip(self):
        for partner in self:
            partner.zip = partner.zip_id and partner.zip_id.name or False

    @api.multi
    @api.depends('street_id.name', 'street_number_id.name')
    def _compute_street(self):
        """Calcul le nom de la rue avec son numéro.

        :return: Une chaine contenant le numéro (s'il existe) de la rue concaténé à l'adresse
        :rtype: string
        """
        for partner in self:
            address_fragment = []
            if partner.street_number_id and partner.street_number_id.name:
                address_fragment.append(partner.street_number_id.name)
            if partner.street_id and partner.street_id.name:
                address_fragment.append(partner.street_id.name)

            partner.street = ' '.join([_f for _f in address_fragment if _f])

    @api.depends('street_id.state', 'city_id.state', 'zip_id.state', 'country_id', 'state_id', 'street_number_id')
    def get_address_status(self):
        """Get the status of the address."""
        protected_countries = self.env['res.config.settings'].get_protected_countries_ids()
        for rec in self:
            status = 'confirmed'
            address_field = [rec.city_id, rec.zip_id, rec.street_id]
            if rec.country_id and rec.country_id.id in protected_countries.ids:
                if not all(address_field):
                    status = 'incomplete'
                elif any([field.state == 'invalidated' for field in address_field]):
                    status = 'invalidated'
                elif any([field.state == 'draft' for field in address_field]):
                    status = 'to_confirm'
                else:
                    status = 'confirmed'
            elif not rec.country_id:
                status = 'incomplete'
            else:
                status = 'confirmed'
            rec.address_status = status

    @api.multi
    @api.depends('street', 'street2', 'city', 'zip', 'country_id.name', 'state_id.name')
    def _compute_better_contact_address(self):
        """Compute the short address display.

        With all the elements of the address used to display the full address in one field.
        """
        for rec in self:
            address = []
            address.append(rec.street or '')
            address.append(rec.street2 or '')
            address.append(rec.street3 or '')
            address.append(rec.city or '')
            address.append(rec.zip or '')
            address.append(rec.state_id and rec.state_id.name or '')
            address.append(rec.country_id and rec.country_id.name or '')
            rec.better_contact_address = ' '.join(' '.join([_f for _f in address if _f]).split(None))

    # endregion

    # region Constrains and Onchange
    @api.onchange('zip_id')
    def onchange_zip_id(self):
        if not self.zip_id:
            self.state_id = False
            self.city_id = False

    @api.onchange('country_id')
    def onchange_country_id(self):
        """Set the state to none if the country of the state and the country are different."""
        if self.country_id and self.state_id:
            if self.state_id.country_id != self.country_id:
                self.state_id = None

    @api.onchange('state_id')
    def onchange_state_id(self):
        """Set the country the same as the country of the state.

        Set the city id to none if city country state and state are different.
        """
        if self.country_id != self.state_id.country_id:
            self.country_id = self.state_id.country_id
        if self.country_id and self.country_id == self.env.ref('base.fr'):
            if self.city_id and self.city_id.country_state_id != self.state_id:
                self.city_id = None

    @api.onchange('city_id')
    def onchange_city_id(self):
        """Onchange method of city_id. Set the zip the same as the zip of the city if the city has only 1 zip.

        Empty the street if the city and the city of the street are different
        """
        self.ensure_one()
        if self.city_id:
            self.state_id = self.city_id.country_state_id
            self.country_id = self.city_id.country_id
            # Si la ville ne contient qu'une adresse zip
            if len(self.city_id.zip_ids) == 1:
                self.zip_id = self.city_id.zip_ids[0]
            # Si la rue à déjà été renseigné mais qu'elle ne correspond pas a la nouvelle ville
            if self.street_id and self.street_id.city_id != self.city_id:
                # Vider le champ street_id
                self.street_id = None

        else:
            self.zip_id = None
            self.street_id = None

    @api.onchange('street_id')
    def onchange_street_id(self):
        """Set the city the same as the city of the street."""
        if self.street_id:
            self.city_id = self.street_id.city_id

    # endregion

    # region CRUD (overrides)
    @api.multi
    def _display_address(self, without_company=False):
        """Override the base methode :meth:`_display_address`.

        To get the address fields value that are
        now on related model (the getattr used in the base method can't use dot notation lookup)
        exemple : getattr(self, 'country_id.name') can't work

        :param without_company: partner record (not a list)
        :return: address string
        :rtype: string
        """
        self.ensure_one()
        # get the information that will be injected into the display format
        # get the address format
        address_format = \
            self.country_id.address_format \
            or "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
        args = self.get_display_address_values(self)
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    @api.model
    def _address_fields(self):
        """Inspired by OCA `partner_street_number <https://github.com/OCA/partner-contact>`_.

        Pass on the fields for address synchronisation to contacts.

        This method is used on at least two occassions:

        [1] when address fields are synced to contacts (:meth:`update_address`, and
        [2] when addresses are formatted (:meth:`_display_address`)

        We want to prevent the 'street', 'street2', 'zip', 'city' fields to be passed in the first case
        (they are now computed or related), as it has a fallback write method which should not be triggered in
        this case, while leaving the field in in the second case. Therefore, we remove the field name from the
        list of address fields unless we find the context key that this module injects when formatting an address.

        Could have checked for the occurrence of the
        synchronisation method instead, leaving the field in by default but that could lead to silent data
        corruption should the synchronisation API ever change.
        """
        address_fields = super(ResPartner, self)._address_fields()
        # remove unwanted fields
        address_fields = [x for x in address_fields if x not in EXCLUDE_ADDRESS_FIELDS]
        # add the new address fields
        address_fields += [x for x in BETTER_ADDRESS_FIELDS if x not in address_fields]
        return address_fields

    @staticmethod
    def get_display_address_values(partner):
        """Utility methode to list all display addresse fields (used for computation).

        :return: fields used by the method :meth:`~._display_address` with their corresponding values
        :rtype: dictionary
        """
        return {
            'street': partner.street or '',
            'street2': partner.street2 or '',
            'zip': partner.zip_id and partner.zip_id.name or partner.zip or '',
            'city': partner.city_id and partner.city_id.name or partner.city or '',
            'street_number': partner.street_number_id and partner.street_number_id.name or '',
            'street_name': partner.street_id and partner.street_id.name or '',
            'state_code': partner.state_id.code or '',
            'state_name': partner.state_id.name or '',
            'country_code': partner.country_id.code or '',
            'country_name': partner.country_id.name or '',
            'company_name': partner.commercial_company_name or '',
        }

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
