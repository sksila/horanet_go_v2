from odoo import api, models, _
from datetime import datetime


class PickupRequestsReport(models.AbstractModel):
    _name = 'report.environment_waste_collect.report_pickup_request'

    def construct_report_datas(self, records):
        """This method build the dict for the report.

        [{'waste_site': waste site name,
          'wastes': [{'name': 'waste name',
                      'service_provider': 'service provider name',
                      'filling_level': {'avg': xx, 'min': xx, 'max': xx},
                      'pickup_delay': {'avg': xx, 'min': xx, 'max': xx},
                      'pickup_time': {'avg': xx, 'min': xx, 'max': xx}
                    }]
          'total': {'filling_level': {'avg': xx, 'min': xx, 'max': xx},
                    'pickup_delay': {'avg': xx, 'min': xx, 'max': xx},
                    'pickup_time': {'avg': xx, 'min': xx, 'max': xx}}
        }]

        :param records: a list of records to put in the dict
        :return: the dict
        """
        liste = []
        total = {}
        total_filling_level_avg = 0
        total_pickup_delay_avg = 0
        total_pickup_time_avg = 0
        total_quantity_avg = 0
        total['filling_level'] = {}
        total['filling_level']['avg'] = 0
        total['filling_level']['min'] = 100000000000
        total['filling_level']['max'] = 0
        total['pickup_delay'] = {}
        total['pickup_delay']['avg'] = 0
        total['pickup_delay']['min'] = 10000000000
        total['pickup_delay']['max'] = 0
        total['pickup_time'] = {}
        total['pickup_time']['avg'] = 0
        total['pickup_time']['min'] = 100000000000
        total['pickup_time']['max'] = 0
        total['quantity'] = {}
        total['quantity']['avg'] = 0
        total['quantity']['min'] = 100000000000
        total['quantity']['max'] = 0
        for waste_site in records.mapped('waste_site_id'):
            dico = {}
            dico['waste_site'] = waste_site.name
            dico['wastes'] = []
            dico['total'] = {}
            dico['total']['filling_level'] = {}
            dico['total']['pickup_delay'] = {}
            dico['total']['pickup_time'] = {}
            dico['total']['quantity'] = {}
            for waste in records.filtered(lambda r: r.waste_site_id == waste_site).mapped('activity_id'):
                dico2 = {}
                dico2['name'] = waste.name
                dico2['service_provider'] = records.filtered(
                    lambda r: r.waste_site_id == waste_site and r.activity_id == waste)[0].service_provider_id.name
                dico2['filling_level'] = {}
                dico2['pickup_delay'] = {}
                dico2['pickup_time'] = {}
                dico2['quantity'] = {}

                dico2['filling_level']['avg'] = sum(
                    records.filtered(lambda r: r.waste_site_id == waste_site and r.activity_id == waste).mapped(
                        'filling_level')) / len(
                    records.filtered(lambda r: r.waste_site_id == waste_site and r.activity_id == waste).mapped(
                        'filling_level'))
                dico2['filling_level']['min'] = min(
                    records.filtered(lambda r: r.waste_site_id == waste_site and r.activity_id == waste).mapped(
                        'filling_level'))
                dico2['filling_level']['max'] = max(
                    records.filtered(lambda r: r.waste_site_id == waste_site and r.activity_id == waste).mapped(
                        'filling_level'))

                # Pour les délais d'enlèvement
                pickups_with_delays = records.filtered(
                    lambda r: r.waste_site_id == waste_site and r.activity_id == waste and r.close_date)
                if pickups_with_delays:
                    pickup_delays = pickups_with_delays.mapped(
                        lambda r: (datetime.strptime(r.close_date, '%Y-%m-%d %H:%M:%S')
                                   - datetime.strptime(r.request_date, '%Y-%m-%d %H:%M:%S')).total_seconds())
                    dico2['pickup_delay']['avg'] = round(sum(pickup_delays) / len(pickup_delays) / 3600.0, 2)
                    dico2['pickup_delay']['min'] = round(min(pickup_delays) / 3600.0, 2)
                    dico2['pickup_delay']['max'] = round(max(pickup_delays) / 3600.0, 2)
                else:
                    dico2['pickup_delay']['avg'] = 0
                    dico2['pickup_delay']['min'] = 0
                    dico2['pickup_delay']['max'] = 0

                # Pour les temps d'enlèvement
                dico2['pickup_time']['avg'] = round(sum(
                    records.filtered(
                        lambda r: r.activity_id == waste).mapped('duration')) / len(
                    records.filtered(lambda r: r.activity_id == waste).mapped('duration')), 2)
                dico2['pickup_time']['min'] = round(min(
                    records.filtered(lambda r: r.activity_id == waste).mapped('duration')), 2)
                dico2['pickup_time']['max'] = round(max(
                    records.filtered(lambda r: r.activity_id == waste).mapped('duration')), 2)

                # Si l'emplacement à un conteneur de spécifié.
                if records.sudo().filtered(lambda r:
                                           r.waste_site_id == waste_site and r.activity_id == waste
                                           and r.emplacement_id.container_type_id.volume):
                    dico2['quantity']['avg'] = dico2['filling_level']['avg'] * records.sudo().filtered(
                        lambda r:
                        r.waste_site_id == waste_site
                        and r.activity_id == waste
                        and r.emplacement_id.container_type_id.volume) \
                        .mapped('emplacement_id.container_type_id.volume')[0] / 100
                    dico2['quantity']['min'] = dico2['filling_level']['min'] * records.sudo().filtered(
                        lambda r:
                        r.waste_site_id == waste_site
                        and r.activity_id == waste
                        and r.emplacement_id.container_type_id.volume) \
                        .mapped('emplacement_id.container_type_id.volume')[0] / 100
                    dico2['quantity']['max'] = dico2['filling_level']['max'] * records.sudo().filtered(
                        lambda r:
                        r.waste_site_id == waste_site
                        and r.activity_id == waste
                        and r.emplacement_id.container_type_id.volume) \
                        .mapped('emplacement_id.container_type_id.volume')[0] / 100
                else:
                    dico2['quantity']['avg'] = 0
                    dico2['quantity']['min'] = 0
                    dico2['quantity']['max'] = 0

                dico['wastes'].append(dico2)

            dico['total']['filling_level']['avg'] = \
                sum(item['filling_level']['avg'] for item in dico['wastes']) / len([v for v in dico['wastes']])
            dico['total']['filling_level']['min'] = \
                min(item['filling_level']['min'] for item in dico['wastes'])
            dico['total']['filling_level']['max'] = \
                max(item['filling_level']['max'] for item in dico['wastes'])
            dico['total']['pickup_delay']['avg'] = \
                sum(item['pickup_delay']['avg'] for item in dico['wastes']) / len([v for v in dico['wastes']])
            dico['total']['pickup_delay']['min'] = \
                min(item['pickup_delay']['min'] for item in dico['wastes'])
            dico['total']['pickup_delay']['max'] = \
                max(item['pickup_delay']['max'] for item in dico['wastes'])
            dico['total']['pickup_time']['avg'] = \
                sum(item['pickup_time']['avg'] for item in dico['wastes']) / len([v for v in dico['wastes']])
            dico['total']['pickup_time']['min'] = \
                min(item['pickup_time']['min'] for item in dico['wastes'])
            dico['total']['pickup_time']['max'] = \
                max(item['pickup_time']['max'] for item in dico['wastes'])
            dico['total']['quantity']['avg'] = \
                sum(item['quantity']['avg'] for item in dico['wastes']) / len([v for v in dico['wastes']])
            dico['total']['quantity']['min'] = \
                min(item['quantity']['min'] for item in dico['wastes'])
            dico['total']['quantity']['max'] = \
                max(item['quantity']['max'] for item in dico['wastes'])

            liste.append(dico)

            total_filling_level_avg += dico['total']['filling_level']['avg']
            if dico['total']['filling_level']['min'] < total['filling_level']['min']:
                total['filling_level']['min'] = dico['total']['filling_level']['min']
            if dico['total']['filling_level']['max'] > total['filling_level']['max']:
                total['filling_level']['max'] = dico['total']['filling_level']['max']

            total_pickup_delay_avg += dico['total']['pickup_delay']['avg']
            if dico['total']['pickup_delay']['min'] < total['pickup_delay']['min']:
                total['pickup_delay']['min'] = dico['total']['pickup_delay']['min']
            if dico['total']['pickup_delay']['max'] > total['pickup_delay']['max']:
                total['pickup_delay']['max'] = dico['total']['pickup_delay']['max']

            total_pickup_time_avg += dico['total']['pickup_time']['avg']
            if dico['total']['pickup_time']['min'] < total['pickup_time']['min']:
                total['pickup_time']['min'] = dico['total']['pickup_time']['min']
            if dico['total']['pickup_time']['max'] > total['pickup_time']['max']:
                total['pickup_time']['max'] = dico['total']['pickup_time']['max']

            total_quantity_avg += dico['total']['quantity']['avg']
            if dico['total']['quantity']['min'] < total['quantity']['min']:
                total['quantity']['min'] = dico['total']['quantity']['min']
            if dico['total']['quantity']['max'] > total['quantity']['max']:
                total['quantity']['max'] = dico['total']['quantity']['max']

        if liste:
            total['filling_level']['avg'] = total_filling_level_avg / len(liste)
            total['pickup_delay']['avg'] = total_pickup_delay_avg / len(liste)
            total['pickup_time']['avg'] = total_pickup_time_avg / len(liste)
            total['quantity']['avg'] = total_quantity_avg / len(liste)

        return liste, total

    def get_pickup_request_report_docargs(self, data, docids=False):
        """This method build the dict for the report.

        :param data: the parameters
        :param docids: docids
        :return: the dict
        """
        report_env = self.env['ir.actions.report']
        report = report_env._get_report_from_name('environment_waste_collect.report_pickup_request')

        domain = []
        date_from = _("Undefined")
        date_to = _("Undefined")

        # We build the domain
        if data['form'].get('waste_site_id', False):
            domain.append(('waste_site_id', '=', data['form']['waste_site_id'][0]))
        if data['form'].get('date_from', False):
            domain.append(('request_date', '>=', data['form']['date_from']))
            date_from = datetime.strptime(data['form']['date_from'], "%Y-%m-%d").date().strftime('%d/%m/%Y')
        if data['form'].get('date_to', False):
            domain.append(('request_date', '<=', data['form']['date_to']))
            date_to = datetime.strptime(data['form']['date_to'], "%Y-%m-%d").date().strftime('%d/%m/%Y')
        if data['form'].get('emplacement_ids', False):
            domain.append(('emplacement_id', 'in', data['form']['emplacement_ids']))
        if data['form'].get('service_provider_id', False):
            domain.append(('service_provider_id', '=', data['form']['service_provider_id'][0]))

        # We search the records according to the domain
        requests = self.env['environment.pickup.request'].search(domain)

        liste, total = self.construct_report_datas(requests)

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': requests,
            'date_from': date_from,
            'date_to': date_to,
            'datas': liste,
            'total': total,
            }

    @api.model
    def get_report_values(self, docids, data=None):
        """We override this function to construct a dict for the report."""
        report_env = self.env['ir.actions.report']
        docargs = self.get_pickup_request_report_docargs(docids=docids, data=data)
        return docargs
