# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

LOCAL_TYPES = [
    ('1', "Maison"),
    ('2', "Appartement"),
    ('3', "Dépendances"),
    ('4', "Local commercial ou industriel"),
]


class LandholdingBati(models.Model):
    """
    This class represents built domains  model.

    A built domain is linked to a communal account, hold by a or several freeholders.
    Each built domain has an address (based on FANTOIR) and a unique_id (10 characters).
    """

    # region Private attributes
    _name = 'landholding.bati'
    _sql_constraints = [('unicity_on_unique_id', 'UNIQUE(unique_id)', _("The unique_id must be unique !"))]
    _rec_name = 'display_address'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    unique_id = fields.Char(
        string="Invariant number",
        required=True,
        index=True,
        copy=False)

    city_id = fields.Many2one(
        string="City",
        comodel_name='res.city',
        domain="[('country_state_id', '=?', state_id), ('zip_ids', 'in', zip_id)]")

    zip_id = fields.Many2one(
        string="Zip code",
        comodel_name='res.zip'
    )

    street_id = fields.Many2one(
        string="Street",
        comodel_name='res.street',
        domain="[('city_id', '=?', city_id)]"
    )

    street2 = fields.Char(string="Additional address")

    street3 = fields.Char(string='Second additional address')

    street_number_id = fields.Many2one(
        string=u"N°",
        comodel_name='res.street.number'
    )

    communal_account_id = fields.Many2one(
        string="Communal account",
        comodel_name='landholding.communal.account'
    )

    country_id = fields.Many2one(
        string="Country",
        comodel_name='res.country')

    state_id = fields.Many2one(
        string="State",
        comodel_name='res.country.state',
        domain="[('city_ids', '=?', city_id)]")

    display_address = fields.Char(string="Address", compute='_get_display_address', store=True)

    local_type = fields.Selection(string="Local type",
                                  selection=LOCAL_TYPES)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def validate_data(self, data):

        communal_account_model = self.env['landholding.communal.account'].sudo()
        res_street_model = self.env['res.street'].sudo()
        res_street_number_model = self.env['res.street.number'].sudo()
        res_city_model = self.env['res.city'].sudo()
        result = list()

        # Hypothèse : tous les enregistrements d'un fichier concernent la même commune
        # On récupère donc celle du premier enregistrement
        if data:
            if data[0].get('state_code', False) and data[0].get('city_insee_code', False):
                city = res_city_model.search([('code', '=', data[0]['state_code'] + data[0]['city_insee_code'])])
                if not city:
                    _logger.warning("The city with code " +
                                    data[0]['state_code'] +
                                    data[0]['city_insee_code'] +
                                    " does not exist")
                    return

                existing_communal_accounts = communal_account_model.search(
                    [('city_id', '=', city.id)])
                existing_streets = res_street_model.search(
                    [('city_id', '=', city.id)])
            else:
                return

        for vals in data:
            # Vérification de présence des données obligatoires
            required_fields = ['street_rivoli_code',
                               'street_number',
                               'communal_account']
            if not all(f in vals.keys() for f in required_fields):
                continue

            del vals['state_code']
            del vals['city_insee_code']

            # Compute address ids
            vals.update({'city_id': city.id})
            vals.update({'state_id': city.country_state_id.id})
            vals.update({'country_id': city.country_id.id})
            vals.update({'zip_id': city.zip_ids.ids[0]})

            # Compute street_id
            street = existing_streets.filtered(lambda r: r.code == vals['street_rivoli_code'])
            if not street:
                _logger.warning("The RIVOLI street code " + vals['street_rivoli_code'] +
                                " for built domain n°" + vals['unique_id'] +
                                " does not exist")
                continue
            vals.update({'street_id': street.id})
            del vals['street_rivoli_code']

            # Compute street2 si appartement
            street2 = vals.get('local_type', False) and vals['local_type'] == '2' and ' '.join([
                vals.get('floor_level', False) and vals['floor_level'].lstrip('0')
                and _("ET. ") + vals['floor_level'].lstrip('0') or '',
                vals.get('door_number', False) and not vals['door_number'] == '01001'
                and _("APPT. ") + vals['door_number'].lstrip('0') or ''
            ]) or ''
            vals.update({'street2': street2})
            del vals['floor_level']
            del vals['door_number']

            # Compute street3 si appartement
            street3 = vals.get('local_type', False) and vals['local_type'] == '2' and ' '.join([
                vals.get('batiment_letter', False) and _("BAT. ") + vals['batiment_letter'] or "",
                vals.get('entree_number', False) and _("ENT. ") + vals['entree_number'].lstrip('0') or ""
            ]) or ''
            vals.update({'street3': street3})
            del vals['batiment_letter']
            del vals['entree_number']

            # Compute street_number_id
            street_number_name = ' '.join([
                vals['street_number'].lstrip('0'),
                vals.get('repetition_code', False) and vals['repetition_code'] or ''
            ])

            street_number = res_street_number_model.search([('name', '=', street_number_name)]) or None
            if not street_number and len(street_number_name) < 4:
                street_number = res_street_number_model.create({'name': street_number_name})

            vals.update({'street_number_id': street_number and street_number.id})
            del vals['street_number']
            del vals['repetition_code']

            # Compute display address
            vals.update({
                'display_address': self.get_display_address(
                    street_number,
                    street,
                    street2,
                    street3,
                    city,
                    city.zip_ids[0],
                    city.country_state_id
                )})

            # Create communal account record if not exists
            communal_account = existing_communal_accounts.filtered(lambda r: r.name == vals['communal_account'])

            if not communal_account:
                _logger.warning("The communal account " + vals['communal_account'] +
                                " for city " + city.name +
                                " does not exist")
                continue

            vals.update({'communal_account_id': communal_account.id})
            del vals['communal_account']

            result.append(vals)

        return result

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

        Set the city id to none if city country state and state are different
        """
        if self.country_id != self.state_id.country_id:
            self.country_id = self.state_id.country_id
        if self.country_id and self.country_id == self.env.ref('base.fr'):
            if self.city_id and self.city_id.country_state_id != self.state_id:
                self.city_id = None

    @api.onchange('city_id')
    def onchange_city_id(self):
        """Onchange method of city_id.

        Set the zip the same as the zip of the city if the city has only 1 zip.
        Empty the street if the city and the city of the street are different
        """
        self.ensure_one()
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

    @api.depends('street_number_id', 'city_id', 'street_id', 'street2', 'street3', 'zip_id', 'state_id')
    def _get_display_address(self):
        """Construct the display address."""
        for rec in self:
            rec.display_address = self.get_display_address(
                rec.street_number_id,
                rec.street_id,
                rec.street2,
                rec.street3,
                rec.city_id,
                rec.zip_id,
                rec.state_id
            )

    # endregion

    # region Model methods
    @staticmethod
    def get_display_address(street_number_id, street_id, street2, street3, city_id, zip_id, state_id):
        """Construct the display address."""
        address_value = [
            street_number_id and street_number_id.name or '',
            street_id and street_id.name or '',
            street2 or '',
            street3 or '',
            zip_id and zip_id.name or '',
            city_id and city_id.name or '',
            state_id and state_id.name or '',
        ]
        display_address = ' '.join(address_value)

        # Une astuce pour que l'on renvoie false si c'est vide.
        if len(' '.join(address_value)) <= 6:
            display_address = False

        return display_address

    # endregion
    pass
