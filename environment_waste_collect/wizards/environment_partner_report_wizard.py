
from odoo import api, fields, models, _
from datetime import datetime, date

DEFAULT_DATE_FORMAT = '%Y-%m-%d'


class EnvironmentPartnerReportWizard(models.TransientModel):
    _name = 'environment.partner.report.wizard'

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To", default=fields.Date.today)
    company_type = fields.Many2many(string="Partner type", comodel_name='subscription.category.partner',
                                    relation='env_partner_wizard_category_rel',
                                    column1='environment_partner_report_wizard', column2='category_partner')
    city_ids = fields.Many2many(string="Cities", comodel_name='res.city')
    access_balance_opt = fields.Selection(string="Access balance criteria",
                                          selection=[('sup', 'Superior to'), ('inf', 'Inferior to')], default='sup')
    access_balance = fields.Integer(string="Access balance")
    access_number_opt = fields.Selection(string="Access number criteria",
                                         selection=[('sup', 'Superior to'), ('inf', 'Inferior to')], default='sup')
    access_number = fields.Integer(string="Access number")

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
        return self.env.ref('environment_waste_collect._report_environment_partner').report_action(self, data=datas)
