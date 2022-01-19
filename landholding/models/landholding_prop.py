# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class LandholdingProp(models.Model):
    """
    This class represents freeholders.

    According to MAJIC files, freeholders have a unique ID (majic_person_number).
    Each freeholder may be part of many communal accounts (see communal account lines).
    These communal account may have many built domains registered.

    We also added freeholder's own address, based on FANTOIR data (i.e. bettre_adress module).
    """

    # region Private attributes
    _name = 'landholding.prop'

    _sql_constraints = [('unicity_on_unique_id', 'UNIQUE(majic_person_number)',
                         _("The majic_person_number must be unique !"))]

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name",
                       required=True)

    majic_person_number = fields.Char(string="Majic person number")

    address_line_1 = fields.Char(string="1st address line")
    address_line_2 = fields.Char(string="2nd address line")
    address_line_3 = fields.Char(string="3rd address line")
    address_line_4 = fields.Char(string="4th address line")

    communal_account_line_ids = fields.One2many(string="Communal accounts",
                                                comodel_name='communal.account.line',
                                                inverse_name='landholding_prop_id')

    landholding_bati_ids = fields.One2many(
        string="Built domains",
        comodel_name='landholding.bati',
        compute='_compute_landholding_bati_ids',
        readonly=True
    )

    # endregion

    # region Fields method
    @api.multi
    @api.depends('communal_account_line_ids')
    def _compute_landholding_bati_ids(self):
        """
        Compute communal accounts of freeholders from their communal account lines.

        A freeholder may be in many communal accounts of many citys and each communal account may have many freeholders.
        Therefore, communal account lines make it possible to join them (with additionnal data such as right codes and
         partial label numbers...)

        :return:
        """
        landholding_bati_model = self.env['landholding.bati'].sudo()

        for rec in self:
            communal_account_ids = rec.communal_account_line_ids.mapped('communal_account_id')
            rec.landholding_bati_ids = landholding_bati_model.search(
                [('communal_account_id', '=', communal_account_ids.ids)]).ids

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

        # On récupère toutes les personnes déjà créées
        landholding_prop_model = self.env['landholding.prop'].sudo()
        existing_props = landholding_prop_model.search([]).mapped('majic_person_number')

        result = list()

        for vals in data:

            del vals['unique_id']

            # Vérification de présence des données obligatoires
            required_fields = ['majic_person_number']
            if not all(f in vals.keys() for f in required_fields):
                continue

            # Si le propriétaire est déjà dans la liste, on passe au suivant
            if vals['majic_person_number'] in existing_props:
                continue
            else:
                existing_props.append(vals['majic_person_number'])

            # Détermination du nom selon si personne physique ou personne morale
            if vals.get('title', False) and vals.get('firstname', False) and vals.get('lastname', False):
                name = ' '.join([vals['title'], vals['firstname'], vals['lastname']])
                vals.update({'name': name})
            elif vals.get('denomination', False):
                name = vals['denomination']
                if vals.get('siren_number', False):
                    name = ''.join([name, ' (', vals['siren_number'], ')'])
                vals.update({'name': name})
            else:
                continue

            del vals['title']
            del vals['firstname']
            del vals['lastname']
            del vals['denomination']
            del vals['siren_number']

            result.append(vals)

        return result

    # endregion

    pass
