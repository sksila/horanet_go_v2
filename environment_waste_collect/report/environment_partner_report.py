
from odoo import api, models, fields, _
from datetime import datetime

DEFAULT_DATE_FORMAT = '%Y-%m-%d'


class PickupRequestsReport(models.AbstractModel):
    _name = 'report.environment_waste_collect.report_environment_partner'

    def construct_report_datas(self, data):  # noqa: C901
        """This method build the dict for the report.

        [{'name': partner name,
          'type': partner type,
          'city': partner city,
          'access_number': the number of access,
          'access_balance': access balance,
          'sales_amount': the amount of sales,
        }]
        :param data: the parameters
        :return: the dict, date from and date to
        """
        domain = [('environment_package_ids', '!=', False)]

        # We build the domain
        if data['form'].get('company_type', False):
            domain.append(('subscription_category_ids', 'in', data['form']['company_type']))
        if data['form'].get('city_ids', False):
            domain.append(('city_id', 'in', data['form']['city_ids']))

        # We search the records according to the domain
        partners = self.env['res.partner'].search(domain, order='company_type, name')
        partner_list = []

        for partner in partners:
            dico = {}

            # Pour le nombre d'accès
            access_count = self.env['horanet.operation'].search([('activity_id.reference', '=', 'ACC'),
                                                                 ('partner_id', '=', partner.id)])
            # On va filtrer le nombre d'accès en fonction des paramètres du wizard
            if data['form'].get('access_number_opt', False):
                if data['form'].get('date_from', False):
                    access_count = access_count.filtered(lambda r: r.time >= data['form']['date_from'])
                if data['form'].get('date_to', False):
                    access_count = access_count.filtered(lambda r: r.time <= data['form']['date_to'])

                if data['form']['access_number_opt'] == 'sup' and len(access_count) < data['form'].get('access_number',
                                                                                                       0):
                    continue
                if data['form']['access_number_opt'] == 'inf' and len(access_count) > data['form'].get('access_number',
                                                                                                       0):
                    continue

            # Pour le solde d'accès, on cherche les packages avec comme activité type 'ACC'
            activity_accesses = self.env['horanet.activity'].search([('reference', '=', 'ACC')])
            domain = [('recipient_id', '=', partner.id), ('prestation_id.activity_ids', 'in', activity_accesses.ids)]
            package_lines = self.env['horanet.package.line'].search(domain)
            # On filtre les packages qui n'ont que l'accès (normalement 1)
            package_lines = package_lines.filtered(lambda r: len(r.prestation_id.activity_ids) == 1)
            if data['form'].get('access_balance_opt', False):
                if data['form']['access_balance_opt'] == 'sup':
                    package_lines = package_lines.filtered(lambda r: r.balance_total >= data['form']['access_balance'])
                if data['form']['access_balance_opt'] == 'inf':
                    package_lines = package_lines.filtered(lambda r: r.balance_total <= data['form']['access_balance'])

                if not package_lines:
                    continue

            access_balance = package_lines[0].balance_total

            # Si le package n'a pas de solde
            if not package_lines[0].is_blocked:
                access_balance = "NA"

            # Pour les ventes
            sales = self.env['sale.order'].search([('partner_id', '=', partner.id)])
            if data['form'].get('date_from', False):
                sales = sales.filtered(lambda r: r.confirmation_date >= data['form']['date_from'] + " 00:00:00")
            if data['form'].get('date_to', False):
                sales = sales.filtered(lambda r: r.confirmation_date <= data['form']['date_to'] + " 23:59:59")

            sales_amount = sum(sales.mapped(lambda r: r.amount_total))

            dico['name'] = partner.name
            dico['type'] = partner.subscription_category_ids[0].name
            dico['city'] = partner.city_id.name
            dico['access_number'] = len(access_count)
            dico['access_balance'] = access_balance
            dico['sales_amount'] = sales_amount

            partner_list.append(dico)

        return partner_list

    @api.model
    def get_report_values(self, docids, data=None):
        """We override this function to construct a dict for the report."""
        partner_list = self.construct_report_datas(data)

        # Additional parameters
        date_to = _("Undefined")
        first_access = self.env['horanet.operation'].search([('activity_id.reference', '=', 'ACC')], order='time',
                                                            limit=1)
        if first_access:
            date_from = datetime.strptime(first_access.time, "%Y-%m-%d %H:%M:%S").date().strftime('%d/%m/%Y')
        else:
            date_from = _("Undefined")
        if data['form'].get('date_from', False):
            date_from = datetime.strptime(data['form']['date_from'], DEFAULT_DATE_FORMAT).date().strftime('%d/%m/%Y')
        if data['form'].get('date_to', False):
            date_to = datetime.strptime(data['form']['date_to'], DEFAULT_DATE_FORMAT).date().strftime('%d/%m/%Y')

        today = datetime.strptime(fields.Date.today(), DEFAULT_DATE_FORMAT).date().strftime('%d/%m/%Y')

        filters_list = []
        if data['form'].get('company_type', False):
            ct = self.env['subscription.category.partner'].search([('id', 'in', data['form']['company_type'])])
            message = _("Partner type(s): ")
            filters_list.append(message + ', '.join(ct.mapped('name')))
        if data['form'].get('city_ids', False):
            cities = self.env['res.city'].search([('id', 'in', data['form']['city_ids'])])
            message = _("Cities: ")
            filters_list.append(message + ', '.join(cities.mapped('name')))
        if data['form'].get('access_balance_opt', False):
            if data['form']['access_balance_opt'] == 'sup':
                message = _("Access balance superior to ")
                filters_list.append(message + str(data['form'].get('access_balance', False)))
            else:
                message = _("Access balance inferior to ")
                filters_list.append(message + str(data['form'].get('access_balance', False)))
        if data['form'].get('access_number_opt', False):
            if data['form']['access_number_opt'] == 'sup':
                message = _("Access number superior to ")
                filters_list.append(message + str(data['form'].get('access_number', False)))
            else:
                message = _("Access number inferior to ")
                filters_list.append(message + str(data['form'].get('access_number', False)))

        docargs = {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': [],
            'date_from': date_from,
            'date_to': date_to,
            'datas': partner_list,
            'today': today,
            'filters': filters_list,
        }
        return docargs
