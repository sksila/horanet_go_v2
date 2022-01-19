# coding: utf-8

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InheritedResPartner(models.Model):
    """Inherited of res.partner model to add horanet_demat_ormc_psv2 informations."""

    # region Private attributes
    _inherit = 'res.partner'

    # endregion

    # region Default methods
    def _get_domain_cat_tiers(self):
        return [('ref_id', '=', self.env.ref('horanet_demat_ormc_psv2.pes_ref_cat_tiers').id)]

    def _get_default_cat_tiers(self):
        is_company = self.env.context.get('default_is_company')

        # In the case the partner shouldn't be a "company"
        if is_company in [0, False]:
            return self.env.ref('horanet_demat_ormc_psv2.pes_ref_cat_tiers_01').id

    def _get_domain_nat_jur(self):
        return [('ref_id', '=', self.env.ref('horanet_demat_ormc_psv2.pes_ref_nat_jur').id)]

    def _get_default_nat_jur(self):
        is_company = self.env.context.get('default_is_company')

        # In the case the partner shouldn't be a "company"
        if is_company in [0, False]:
            return self.env.ref('horanet_demat_ormc_psv2.pes_ref_nat_jur_01').id

    # endregion

    # region Fields declaration
    cat_tiers_id = fields.Many2one(
        'pes.referential.value',
        string='CatTiers',
        help='Value used to fill CatTiers attribute in ORMC file',
        domain=_get_domain_cat_tiers,
        default=_get_default_cat_tiers,
        required=True
    )
    nat_jur_id = fields.Many2one(
        'pes.referential.value',
        string='NatJur',
        help='Value used to fill NatJur attribute in ORMC file',
        domain=_get_domain_nat_jur,
        default=_get_default_nat_jur,
        required=True
    )
    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    @api.constrains('cat_tiers_id', 'nat_jur_id')
    def _check_constraint_cattiers_natjur(self):
        self.ensure_one()

        """Ensure that cat_tier and nat_jur values respect constraint."""
        if self.cat_tiers_id and self.nat_jur_id:
            constraint = self.env['pes.referential.value.constraint'].search([
                ('ref_value_1_id', '=', self.cat_tiers_id.id),
                ('ref_value_2_id', '=', self.nat_jur_id.id),
            ])
            if not constraint:
                valid_cat_tiers_values = self.env['pes.referential.value.constraint'].search([
                    ('ref_value_2_id', '=', self.nat_jur_id.id),
                ])
                valid_nat_jur_values = self.env['pes.referential.value.constraint'].search([
                    ('ref_value_1_id', '=', self.cat_tiers_id.id),
                ])

                raise ValidationError(_(
                    "CatTiers and NatJur values are not consistent.\n\n"
                    "Valid values of NatJur for CatTiers '{cat_tiers}':\n{valid_nat_jur_values}\n\n"
                    "Valid values of CatTiers for NatJur '{nat_jur}':\n{valid_cat_tiers_values}").format(
                    cat_tiers=self.cat_tiers_id.name,
                    nat_jur=self.nat_jur_id.name,
                    valid_cat_tiers_values='\n'.join(
                        ['- ' + v.name for v in valid_cat_tiers_values.mapped('ref_value_1_id')]),
                    valid_nat_jur_values='\n'.join(
                        ['- ' + v.name for v in valid_nat_jur_values.mapped('ref_value_2_id')])
                ))
    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        u"""Surcharge du create pour renseigner le cat tiers et nat jur pour les particuliers.

        On passe par une surcharge afin de traiter les inscriptions via le front. Lorsque l'on crée un partner, la
        condition "is_company = self.env.context.get('default_is_company')" des defaults ne marche pas car on passe
        par le template citoyen (qui est un particulier) même si le partner est une société.
        """
        if not vals.get('is_company', False) and not vals.get('cat_tiers_id', False) \
                and not vals.get('nat_jur_id', False):
            vals['cat_tiers_id'] = self.env.ref('horanet_demat_ormc_psv2.pes_ref_cat_tiers_01').id
            vals['nat_jur_id'] = self.env.ref('horanet_demat_ormc_psv2.pes_ref_nat_jur_01').id

        return super(InheritedResPartner, self).create(vals)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
