# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class LandholdingCommunalAccount(models.Model):
    """This class represents communal accounts model."""

    # region Private attributes
    _name = 'landholding.communal.account'
    # _sql_constraints = [('unicity_on_unique_id', 'UNIQUE(unique_id)',
    #                      _("The unique_id must be unique !"))]

    _sql_constraints = [('unicity_on_name_and_city', 'UNIQUE(name, city_id)',
                         _("The name + city_id must be unique !"))]

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Communal account",
        required=True,
        copy=False)

    city_id = fields.Many2one(
        string="City",
        required=True,
        comodel_name='res.city')

    communal_account_line_ids = fields.One2many(string="Freeholders",
                                                comodel_name='communal.account.line',
                                                inverse_name='communal_account_id')
    landholding_bati_ids = fields.One2many(string="Built domains",
                                           comodel_name='landholding.bati',
                                           inverse_name='communal_account_id')

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

        res_city_model = self.env['res.city'].sudo()
        communal_account_model = self.env['landholding.communal.account'].sudo()

        existing_communal_accounts = list()
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
                    [('city_id', '=', city.id)]).mapped('name')
            else:
                return

        for vals in data:
            # Vérification de présence des données obligatoires
            if not vals.get('communal_account', False):
                continue

            del vals['unique_id']
            del vals['state_code']
            del vals['city_insee_code']
            vals.update({'city_id': city.id})

            # Create communal account record if not exists
            # => Si le compte communal existe déjà en base ou dans le fichier en cours de traitement,
            # on passe au suivant
            if vals['communal_account'] in existing_communal_accounts:
                continue

            # Ajout dans la liste
            existing_communal_accounts.append(vals['communal_account'])

            vals.update({'name': vals['communal_account']})
            del vals['communal_account']

            result.append(vals)

        return result

    # endregion

    pass
