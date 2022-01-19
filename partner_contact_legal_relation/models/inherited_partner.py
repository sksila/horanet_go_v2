import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration

    # my garants ==> partner whom the current partner is under the responsibility
    # use relation attribute since implicit/canonical naming of many2many relationship table
    # is not possible when source and destination models are the same (col1 = these, col2 = those)
    garant_ids = fields.Many2many(
        string="Under responsability of",
        comodel_name='res.partner',
        relation='res_partner_responsability_rel',
        column1='garant_id',
        column2='dependant_id',
        copy=False,
        readonly=True)

    # my dependants ==> partner whom the current partner has the responsibility
    dependant_ids = fields.Many2many(
        string="Responsible for",
        relation='res_partner_responsability_rel',
        column1='dependant_id',
        column2='garant_id',
        comodel_name='res.partner',
        domain="[('is_company', '=', False), ('id', '!=', id), ('id', 'not in', garant_ids and garant_ids[0][2])]",
        copy=False)

    is_responsible = fields.Boolean(
        string="Is responsible",
        compute='_compute_is_responsible',
        store=False)

    # endregion

    # region Fields method
    @api.depends('dependant_ids', 'garant_ids')
    def _compute_is_responsible(self):
        """Compute the responsability of a partner."""
        for rec in self:
            is_responsible = True
            if rec.dependant_ids and len(rec.garant_ids) == 0:
                is_responsible = False
            rec.is_responsible = is_responsible

    # endregion

    # region Constrains and Onchange

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
