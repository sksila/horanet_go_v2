
from odoo import api, fields, models


class PickupRequestReport(models.TransientModel):

    _name = 'environment.pickup.request.wizard'

    waste_site_id = fields.Many2one(string="Waste site", comodel_name='environment.waste.site')
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To", default=fields.Date.today)
    emplacement_ids = fields.Many2many(string="Emplacement", comodel_name='stock.emplacement')
    service_provider_id = fields.Many2one(string="Service provider", comodel_name='res.partner',
                                          domain="[('is_environment_service_provider', '=', True)]")

    @api.multi
    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'environment.pickup.request',
            'form': data
        }
        return self.env.ref('environment_waste_collect.pickup_request_report').report_action(self, data=datas)

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
            'report_name': 'environment_waste_collect.xlsx_report_pickup_request.xlsx',
            'datas': datas,
        }
