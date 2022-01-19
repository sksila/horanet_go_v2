# -*- coding: utf-8 -*-

import base64
import json
import urllib

import requests

from odoo import fields, models, api, _
from odoo.exceptions import UserError


def geo_find(street, city, zipcode):
    # On utilise l'api du gouvernement français pour localiser une adresse
    url = 'https://api-adresse.data.gouv.fr/search/?q='
    url += street + ' ' + city
    if zipcode:
        url += '&postcode=' + zipcode
    url += '&limit=1'

    try:
        result = json.load(urllib.urlopen(url))
    except Exception as e:
        raise UserError(_(
            'Cannot contact geolocation servers. Please make sure that your Internet connection is up '
            'and running (%s).') % e)

    # Si aucun résultat
    if not result.get('features'):
        return None
    # Si résultat insuffisant (score < 50%)
    elif result.get('features')[0].get('properties').get('score') < 0.50:
        return None

    try:
        geo = result['features'][0].get('geometry').get('coordinates')
        # On retourne la latitude et la longitude (dans cet ordre)
        return float(geo[1]), float(geo[0])
    except (KeyError, ValueError):
        return None


class ProductionPoint(models.Model):
    # region Private attributes
    _name = 'production.point'
    _sql_constraints = [('unicity_on_address', 'UNIQUE(display_address)', _('The address must be unique'))]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", copy=False, compute='_compute_name', store=True)
    partner_id = fields.Many2one(string="Owner", comodel_name='res.partner')
    display_address = fields.Char(string="Address", compute='_get_display_address', store=True,
                                  track_visibility='onchange')
    city_id = fields.Many2one(string="City", comodel_name='res.city',
                              domain="[('country_state_id', '=?', state_id), ('zip_ids', 'in', zip_id)]")
    zip_id = fields.Many2one(string="Zip code", comodel_name='res.zip')
    street_id = fields.Many2one(string="Street", comodel_name='res.street', domain="[('city_id', '=?', city_id)]")
    street2 = fields.Text(string="Additional address 2")
    street3 = fields.Text(string="Additional address 3")
    street_number_id = fields.Many2one(string=u"N°", comodel_name='res.street.number')
    country_id = fields.Many2one(string="Country", comodel_name='res.country')
    state_id = fields.Many2one(string="State", comodel_name='res.country.state')
    localisation_map = fields.Binary(string="Localisation")

    partner_move_ids = fields.One2many(
        string="Moves",
        comodel_name='partner.move',
        inverse_name='production_point_id')

    attribution_partner_ids = fields.Many2many(string="Attribution partners", comodel_name='res.partner', store=True,
                                               compute='compute_attribution_partners')

    # endregion

    # region Fields method
    @api.depends('partner_move_ids')
    def compute_attribution_partners(self):
        """Get all the partner related to his attributions."""
        for rec in self:
            if rec.partner_move_ids:
                rec.attribution_partner_ids = rec.partner_move_ids.mapped('partner_id')

    @api.depends('street_number_id', 'city_id', 'street_id', 'zip_id', 'state_id', 'street2', 'street3')
    def _get_display_address(self):
        """Construct the display address."""
        for rec in self:
            address_value = [
                rec.street_number_id and rec.street_number_id.name or '',
                rec.street_id and rec.street_id.name or '',
                rec.street2 or '',
                rec.street3 or '',
                rec.city_id and rec.city_id.name or '',
                rec.zip_id and rec.zip_id.name or '',
                rec.state_id and rec.state_id.name or '',
            ]
            rec.display_address = ' '.join(address_value)

            # Une astuce pour que l'on renvoie false si c'est vide.
            if len(' '.join(address_value)) <= 6:
                rec.display_address = False

    # endregion

    # region Constrains and Onchange
    @api.onchange('display_address')
    @api.depends('display_address')
    def _compute_name(self):
        """Set the name."""
        for rec in self.filtered('display_address'):
            rec.name = rec.display_address

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

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_geolocalize(self):
        """Call the compute to create the map from an address."""
        self.localisation_google_map_img()

    # endregion

    # region Model methods
    @api.multi
    def localisation_google_map_img(self, zoom=16, width=400, height=270):
        """
        Create the google map of the coordinates from the attribution point.

        :param zoom: the zoom of the map
        :param width: the width of the map
        :param height: the height of the map
        :return: nothing
        """
        for rec in self.filtered('display_address'):
            # On fait une 1ère recherche avec tout les paramètres
            result = geo_find(street=rec.street_id.name, city=rec.city_id.name, zipcode=rec.zip_id.name)

            # Si pas de résultat, on réessaye mais sans le CP
            if not result:
                result = geo_find(street=rec.street_id.name, city=rec.city_id.name, zipcode=False)

            if result:
                image_url = "https://maps.googleapis.com/maps/api/staticmap?zoom={}&size={}x{}&markers=" \
                            "color:red%7Clabel:O%7C{},{}".format(zoom, width, height, result[0], result[1])
                rec.localisation_map = base64.b64encode(requests.get(image_url).content)
        return True

    # endregion
    pass
