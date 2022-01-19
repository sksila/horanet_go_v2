# coding: utf-8

from odoo import models, fields, api, _, exceptions


class InheritedHoranetBudgetCode(models.Model):
    # region Private attributes
    _inherit = 'horanet.budget.code'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    ormc_cod_bud = fields.Char(
        string='CodBud',
        help='Value used to fill CodBud attribute in ORMC file',
        required=True
    )
    ormc_libelle_cod_bud = fields.Char(
        string='LibelleCodBud',
        help='Value used to fill LibelleCodBud attribute in ORMC file',
        required=True
    )

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    @api.constrains('ormc_cod_bud')
    def _check_ormc_cod_bud(self):
        for rec in self:
            if len(rec.ormc_cod_bud) > 2:
                raise exceptions.ValidationError(
                    _("The CodBud must be on two characters maximum.")
                )
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
