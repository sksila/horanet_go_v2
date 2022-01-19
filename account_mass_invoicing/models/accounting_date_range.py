# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class HoranetAccountingDateRange(models.Model):
    """This model represent a fiscal year."""

    # region Private attributes
    _name = 'horanet.accounting.date.range'
    # endregion

    # region Default methods
    def _get_default_year(self):
        num = datetime.now().year
        return num
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", compute='_compute_name')
    accounting_year = fields.Selection(string="Year of the fiscal year",
                                       selection=[(num, str(num)) for num in range(((datetime.now().year)-5),
                                                                                   ((datetime.now().year)+3))],
                                       default=_get_default_year,
                                       )

    company_id = fields.Many2one(string="Company", comodel_name='res.company')
    start_date = fields.Date(string="Start date of the fiscal year", compute='_compute_start_end_date')
    end_date = fields.Date(string="End date of the fiscal year", compute='_compute_start_end_date')

    # endregion

    # region Fields method
    @api.depends('accounting_year', 'start_date', 'end_date')
    def _compute_name(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                parts = [
                    p for p in [rec.start_date.replace('-', '/'), rec.end_date.replace('-', '/'),
                                rec.company_id.name] if p
                ]
                rec.name = ' - '.join(parts)

    @api.depends('accounting_year', 'company_id')
    def _compute_start_end_date(self):
        """Set the start date and the end date of the fiscal year.

        The start date and the end date are based on the fields fiscalyear_last_month, fiscalyear_last_day of
        res.compnay (these fields set the last day of the fiscal year) and accounting_year.
        A fiscal year is equal to one year.
        """
        for rec in self:
            if rec.company_id:
                company = self.env['res.company'].browse(rec.company_id.id)

                fiscal_year_year = dict(rec._fields['accounting_year'].selection).get(rec.accounting_year)
                fiscal_year_month = company.fiscalyear_last_month
                fiscal_year_day = company.fiscalyear_last_day
                fiscal_year_date = fields.Date.from_string(fiscal_year_year + '-' + str(fiscal_year_month) + '-' +
                                                           str(fiscal_year_day))

                rec.end_date = fiscal_year_date
                rec.start_date = fiscal_year_date - relativedelta(years=1) + relativedelta(days=1)

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
