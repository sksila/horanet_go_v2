import base64

import requests

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class HoranetInfrastructure(models.Model):
    # region Private attributes
    _name = 'horanet.infrastructure'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name",
        required=True)
    check_point_ids = fields.One2many(
        string="Check points",
        comodel_name='device.check.point',
        inverse_name='infrastructure_id')
    description = fields.Text(
        string="Description")

    city_id = fields.Many2one(string="City", comodel_name="res.city", help="select the city",
                              domain="[('country_state_id', '=?', state_id), ('zip_ids', 'in', zip_id)]")
    street_id = fields.Many2one(string="Street", comodel_name='res.street', domain="[('city_id', '=?', city_id)]")
    zip_id = fields.Many2one(string="ZIP code", comodel_name='res.zip', domain="[('city_ids', '=?', city_id)]")
    street_number_id = fields.Many2one(string="N°", comodel_name='res.street.number')
    street2 = fields.Char(string="Additional address")
    country_id = fields.Many2one(string="Country", comodel_name='res.country')
    state_id = fields.Many2one(string="State", comodel_name='res.country.state')
    display_address = fields.Char(string="Address", compute='_get_display_address', store=False)

    longitude = fields.Float(string='Longitude', digits=dp.get_precision('Waste site localisation decimal'))
    latitude = fields.Float(string='Latitude', digits=dp.get_precision('Waste site localisation decimal'))
    localisation_map = fields.Binary(string="Localisation", compute='localisation_google_map_img', store=True)

    configuration_json = fields.Text(
        string="Configuration",
        default='---',
        help="Configuration to be send to the device, regarding the equipment in-situ (like IP address)",
    )
    # endregion

    # region Fields method
    @api.depends('street_number_id', 'city_id', 'street_id', 'state_id')
    def _get_display_address(self):
        for rec in self:
            address_value = [
                rec.street_number_id and rec.street_number_id.name or '',
                rec.street_id and rec.street_id.name or '',
                rec.city_id and rec.city_id.name or '',
                rec.state_id and rec.state_id.name or '',
            ]
            rec.display_address = ' '.join(address_value)

    @api.depends('latitude', 'longitude')
    def localisation_google_map_img(self, zoom=16, width=350, height=300):
        """
        Create the google map of the coordinates.

        :param zoom: the zoom of the map
        :param width: the width of the map
        :param height: the height of the map
        :return: nothing
        """
        for rec in self:
            if rec.latitude and rec.longitude:
                image_url = "https://maps.googleapis.com/maps/api/staticmap?zoom={}&size={}x{}&markers=" \
                            "color:red%7Clabel:O%7C{},{}".format(zoom, width, height, rec.latitude, rec.longitude)
                rec.localisation_map = base64.b64encode(requests.get(image_url).content)

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
        """
        Set the country the same as the country of the state.

        Set the city id to none if city country state and state are different
        """
        if self.country_id != self.state_id.country_id:
            self.country_id = self.state_id.country_id
        if self.country_id and self.country_id == self.env.ref('base.fr'):
            if self.city_id and self.city_id.country_state_id != self.state_id:
                self.city_id = None

    @api.onchange('city_id')
    def onchange_city_id(self):
        """
        Onchange method of city_id. Set the zip the same as the zip of the city if the city has only 1 zip.

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
    # endregion

    # region Model methods
    # endregion

    pass
