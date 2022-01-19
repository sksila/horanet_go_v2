# -*- coding: utf-8 -*-

import json
import urllib
import unidecode

from odoo import models, fields, api, _
from odoo.exceptions import UserError


def geo_find(street, city, zipcode):
    # On utilise l'api du gouvernement français pour localiser une adresse
    if not street:
        return None

    url = 'https://api-adresse.data.gouv.fr/search/?q='
    url += unidecode.unidecode(street)
    # Si on met en plus la ville
    if city:
        url += ' ' + city
    # Si on met en plus le zip
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


class TCOInscription(models.Model):
    """We add fields and change some methods."""

    # region Private attributes
    _inherit = 'res.partner'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    is_als = fields.Boolean(string="ALS", default=False)
    inscription_ids = fields.One2many(string="Inscriptions", comodel_name="tco.inscription.transport.scolaire",
                                      inverse_name='recipient_id')
    has_custom_image = fields.Boolean(string='Has custom avatar')
    is_als_organism = fields.Boolean(string="Is a social service organism")
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def write(self, vals):
        """We check if the partner has a custom profile picture or not."""
        if 'image' in vals.keys():
            if not vals.get('image', False):
                vals['has_custom_image'] = False
            else:
                vals['has_custom_image'] = True
        return super(TCOInscription, self).write(vals)

    # endregion

    # region Actions
    @api.multi
    def geo_localize(self):
        """We override this function to use an other way of geocoding."""
        for partner in self.with_context(lang='en_US'):
            # On fait une 1ère recherche avec tout les paramètres
            result = geo_find(street=partner.street, city=partner.city, zipcode=partner.zip)

            # Si pas de résultat, on réessaye mais sans le CP
            if not result:
                result = geo_find(street=partner.street_id.name, city=partner.city, zipcode=False)

            if result:
                partner.write({
                    'partner_latitude': result[0],
                    'partner_longitude': result[1],
                    'date_localization': fields.Date.context_today(partner)
                })
    # endregion

    # region Model methods
    # endregion

    pass
