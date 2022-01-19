# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

RIGHT_CODES = [
    ('P', "Propriétaire"),
    ('U', "Usufruitier"),
    ('N', "Nu-propriétaire"),
    ('B', "Bailleur à construction"),
    ('R', "Preneur à construction"),
    ('F', "Foncier"),
    ('T', "Ténuyer"),
    ('D', "Domanier"),
    ('V', "Bailleur d\'un bail à réhabilitation"),
    ('W', "Preneur d\'un bail à réhabilitation"),
    ('A', "Locataire-attributaire"),
    ('E', "Emphytéole"),
    ('K', "Antichrésiste"),
    ('L', "Fonctionnaire logé"),
    ('G', "Gérant, madataire, gestionnaire"),
    ('S', "Syndic de copropriété"),
    ('H', "Associé dans une société en transparence fiscale"),
    ('O', "Autorisation d\'occupation temporaire"),
    ('J', "Jeune agriculteur"),
    ('Q', "Gestionnaire taxe sur les bureaux"),
    ('X', "La poste, propriétaire et occupant"),
    ('Y', "La poste, occupant et non propriétaire"),
    ('C', "Fiduciaire"),
    ('M', "Occupant d\'une parcelle appartenant au département de Mayotte ou à l\'état"),
]


class LandholdingCommunalAccountLine(models.Model):
    """
    Join freeholders and communal accounts.

    A freeholder may be in many communal accounts of many citys and each communal account may have many freeholders.
    Therefore, communal account lines make it possible to join them (with additionnal data such as right codes and
      partial label numbers...)
    """

    # region Private attributes
    _name = 'communal.account.line'
    _sql_constraints = [('unicity_on_unique_id', 'UNIQUE(communal_account_id, partial_label_number)',
                         _("The communal_account_id + partial_label_number must be unique !"))]

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    partial_label_number = fields.Char(
        string="Partial label number"
    )

    landholding_prop_id = fields.Many2one(string="Freeholder",
                                          comodel_name='landholding.prop')

    communal_account_id = fields.Many2one(string="Communal account",
                                          comodel_name='landholding.communal.account')

    city_id = fields.Many2one(
        string="City",
        related='communal_account_id.city_id',
        readonly=True
    )

    real_part_right_code = fields.Selection(RIGHT_CODES,
                                            string="Real or particular right",
                                            required=True)

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
        landholding_prop_model = self.env['landholding.prop'].sudo()

        result = list()

        for vals in data:
            # Vérification de présence des données obligatoires
            required_fields = ['majic_person_number',
                               'state_code',
                               'city_insee_code',
                               'communal_account']
            if not all(f in vals.keys() for f in required_fields):
                continue

            del vals['unique_id']

            # Détermination du propriétaire via son numéro MAJIC
            landholding_prop = landholding_prop_model.search(
                [('majic_person_number', '=', vals['majic_person_number'])])
            if not landholding_prop:
                continue
            del vals['majic_person_number']
            vals.update({'landholding_prop_id': landholding_prop.id})

            # Create communal account record if not exists
            # => Compute city_id
            city = res_city_model.search([('code', '=', vals['state_code'] + vals['city_insee_code'])])
            if not city:
                _logger.warning("The city with code " +
                                vals['state_code'] +
                                vals['city_insee_code'] +
                                " does not exist")
                continue
            del vals['state_code']
            del vals['city_insee_code']

            # => Compute communal_account_id
            communal_account = communal_account_model.search([('city_id', '=', city.id),
                                                              ('name', '=', vals['communal_account'])])
            if not communal_account:
                communal_account = communal_account_model.create({
                    'city_id': city.id,
                    'name': vals['communal_account']
                })

            del vals['communal_account']
            vals.update({'communal_account_id': communal_account.id})

            result.append(vals)

        return result

    # endregion

    pass
