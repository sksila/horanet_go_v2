# -*- coding: utf-8 -*-

from odoo import api, fields, models

COMPANY_TYPES = (('epci', 'EPCI'), ('municipality', 'Municipality'), ('company', 'Company'))


class ResCompany(models.Model):
    # region Private attributes
    _inherit = 'res.company'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    municipality_ids = fields.Many2many(
        string="Municipalities",
        comodel_name='res.company',
        relation='res_company_epci_municipality_rel',
        column1='epci_id',
        column2='municipality_id',
    )
    epci_ids = fields.Many2many(
        string="EPCI",
        comodel_name='res.company',
        relation='res_company_epci_municipality_rel',
        column1='municipality_id',
        column2='epci_id',
    )
    type_company = fields.Selection(
        string="Company type",
        selection=COMPANY_TYPES,
        default='company',
        compute='_compute_type_company',
        search='_search_type_company',
        store=False,
    )
    # endregion

    # region Fields method
    @api.multi
    @api.depends('municipality_ids', 'epci_ids')
    def _compute_type_company(self):
        """Set the type of the company corresponding to its properties."""
        for rec in self:
            type_company = 'company'

            if rec.municipality_ids:
                type_company = 'epci'
            elif rec.epci_ids:
                type_company = 'municipality'

            rec.type_company = type_company

    @api.model
    def _search_type_company(self, operator, value):
        companies = None

        if value == 'epci':
            companies = self.search([('municipality_ids', '!=', False)])
        elif value == 'municipality':
            companies = self.search([('epci_ids', '!=', False)])

        return [('id', 'in', companies.ids)]
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
