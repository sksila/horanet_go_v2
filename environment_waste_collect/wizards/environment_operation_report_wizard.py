# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, date

DEFAULT_DATE_FORMAT = '%Y-%m-%d'


class EnvironmentOperationReportWizard(models.TransientModel):
    """Wizard to create environment partner report."""

    _name = 'environment.operation.report.wizard'

    def _default_action_id(self):
        return self.env.ref('horanet_subscription.action_passage').id

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To", default=fields.Date.today)
    partner_category = fields.Many2many(
        string="Partner type",
        comodel_name='subscription.category.partner',
        relation='env_operation_wizard_category_rel',
        column1='environment_operation_report_wizard',
        column2='category_partner',
    )

    infrastructure_ids = fields.Many2many(
        string="Infrastructure(s)",
        comodel_name='horanet.infrastructure',
    )

    activity_ids = fields.Many2many(
        string="Activities",
        comodel_name='horanet.activity',
    )

    action_number_opt = fields.Selection(
        string="Action number criteria",
        selection=[('sup', 'Superior or equal to'), ('inf', 'Inferior or equal to')],
        default='sup',
    )
    action_number = fields.Integer(string="Action number")
    action_id = fields.Many2one(
        string="Action",
        comodel_name='horanet.action',
        default=_default_action_id,
        help="By default: Action passage",
    )

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        """We prevent the user to set weird dates."""
        if self.date_from and self.date_to:
            date_from = datetime.strptime(self.date_from, DEFAULT_DATE_FORMAT).date()
            date_to = datetime.strptime(self.date_to, DEFAULT_DATE_FORMAT).date()
            if date_from > date_to:
                self.date_from = False
                self.date_to = fields.Date.today()
                return {
                    'warning': {'title': _("Warning"),
                                'message': _("You can't set a date to inferior to the date from.")},
                }
            elif date_to > date.today():
                self.date_to = fields.Date.today()
                return {
                    'warning': {'title': _("Warning"),
                                'message': _("You can't set a date to superior to the current date.")},
                }

    @api.multi
    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'res.partner',
            'form': data
        }
        return self.env['report'].get_action(False, 'environment_waste_collect.report_environment_operation',
                                             data=datas)

    @api.multi
    def print_xls_report(self):
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'res.partner',
            'form': data
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'environment_waste_collect.xlsx_report_environment_operation.xlsx',
            'datas': datas,
        }
