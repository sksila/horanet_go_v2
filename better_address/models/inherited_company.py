import logging
from collections import defaultdict

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """res.company inheritance to add better address fields."""

    # region Private attributes
    _inherit = 'res.company'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    city_id = fields.Many2one(
        string='City',
        comodel_name='res.city',
        compute='_compute_better_address',
        inverse='_inverse_city_id',
        help="select the city",
        store=False)
    street_id = fields.Many2one(
        string='Street',
        comodel_name='res.street',
        compute='_compute_better_address',
        inverse='_inverse_street_id',
        domain="[('city_id', '=?', city_id)]",
        store=False)
    zip_id = fields.Many2one(
        string='ZIP',
        comodel_name='res.zip',
        compute='_compute_better_address',
        inverse='_inverse_zip_id',
        domain="[('city_ids', '=?', city_id)]",
        store=False)
    street_number_id = fields.Many2one(
        string='N°',
        comodel_name='res.street.number',
        compute='_compute_better_address',
        inverse='_inverse_street_number_id',
        store=False)
    street2 = fields.Char(
        string='Additional address')

    # endregion

    # region Fields method
    @api.multi
    def _compute_better_address(self):
        """Equivalent de la fonction _get_address_data du model de base.

        Permet de récupérer les champs d'adresse du partner liée a la company
        :return: Nothing,
        """
        for company in self.filtered(lambda company: company.partner_id):
            address_data = company.partner_id.sudo().address_get(adr_pref=['contact'])
            if address_data['contact']:
                partner = company.partner_id.browse(address_data['contact'])
                company.street_number_id = partner.street_number_id
                company.street_id = partner.street_id
                company.street2 = partner.street2
                company.city_id = partner.city_id
                company.zip_id = partner.zip_id

    @api.multi
    def _inverse_city_id(self):
        for company in self:
            company.partner_id.city_id = company.city_id.id

    @api.multi
    def _inverse_street_id(self):
        for company in self:
            company.partner_id.street_id = company.street_id.id

    @api.multi
    def _inverse_zip_id(self):
        for company in self:
            company.partner_id.zip_id = company.zip_id.id

    @api.multi
    def _inverse_street_number_id(self):
        for company in self:
            company.partner_id.street_number_id = company.street_number_id.id

    # endregion

    # region Constrains and Onchange
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
        """Onchange method of city_id."""
        if self.city_id:
            self.state_id = self.city_id.country_state_id
            self.country_id = self.city_id.country_id
            # Si la ville ne contient qu'une adresse zip
            if len(self.city_id.zip_ids) == 1:
                self.zip_id = self.city_id.zip_ids[0]
            if len(self.city_id.zip_ids) > 1:
                self.zip_id = None
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
    def onchange(self, values, field_name, field_onchange):
        """Override of the base method :meth:`model.Model.onchange`.

        to add the possibility to force a field to be dirty

        A dirty field will be send to the view for update after an onchange
        event, to use this override the key 'force_dirty' must be added
        to the context.

        Use case : force a Many2one field to have a name for the selection
        drop-down different than it's regular name

        :param values: dictionary mapping field names to values, giving the
            current state of modification
        :param field_name: name of the modified field, or list of field
            names (in view order), or False
        :param field_onchange: dictionary mapping field names to their
            on_change attribute
        """
        res = super(ResCompany, self).onchange(values, field_name, field_onchange)
        context = self.env.context or {}
        if context.get('force_dirty') and values.get(field_name):
            # create a new record with values, and attach ``self`` to it
            with self.env.do_in_onchange():
                record = self.new(values)

                def dct_structure():
                    return defaultdict(dct_structure)
                names = dct_structure()
                onchange_tuple = self._fields[field_name].convert_to_onchange(record[field_name], self, names)
                res['value'].update({field_name: onchange_tuple})
        return res

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
