# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from datetime import datetime
from odoo.osv import expression
from itertools import groupby

DEFAULT_DATE_FORMAT = '%Y-%m-%d'


class OperationRequestsReport(models.AbstractModel):
    """Class for the environment Operation report."""

    _name = 'report.environment_waste_collect.report_environment_operation'

    def construct_operation_report_datas(self, data):
        """This method build the partner data dict for the environment operation report.

        [{'name': partner name,
          'type': partner type,
          'infrastructure': infrastructure of the partner actions,
          'activity': activities for the action, if depot we list the differents activities,
          'unit': unit of measure,
          'action_number': the number or the quantity (for depot) of the action,
        }]

        :param data: the parameters
        :return: the dict, date from and date to
        """
        # We define the partner search domain
        domain = []
        partner_list = []
        category_domain = []
        form = data['form']

        # subscription category filter
        if form.get('partner_category', False):
            for partner_category in form['partner_category']:
                category_domain.append([('partner_sub_category_ids', 'in', [partner_category])])
            category_domain = expression.OR(category_domain)

        # operation action filter
        if form.get('action_id', False):
            action_id = form['action_id'][0]
        else:
            action_id = self.env.ref('horanet_subscription.action_passage').id
        domain.append(('action_id', '=', action_id))

        # operation infrastructure filter
        if form.get('infrastructure_ids', False):
            domain.append(('infrastructure_id', 'in', form['infrastructure_ids']))

        # operation activity filter
        if form.get('activity_ids', False):
            domain.append(('activity_id', 'in', form['activity_ids']))

        # operation time filter
        if form.get('date_from', False):
            domain.append(('time', '>=', form['date_from']))

        if form.get('date_to', False):
            domain.append(('time', '<=', form['date_to']))

        # operation computed filter
        domain.append(('disable_computation', '=', False))

        operations_set = self.env['horanet.operation'].search(category_domain + domain).sorted(
            key=lambda operation: operation.operation_partner_id.id
        )

        operations_groupby_partner = [(partner, [o for o in operations]) for partner, operations in
                                      groupby(operations_set, lambda p: p.operation_partner_id)]

        depot_action_id = self.env.ref('environment_waste_collect.horanet_action_depot').id
        for operations_by_partner in operations_groupby_partner:
            dico = {}
            partner = operations_by_partner[0]
            operations = operations_by_partner[1]

            # Processus for depot action
            if action_id == depot_action_id:
                type = partner.subscription_category_ids[0].name if partner.subscription_category_ids else "NA"
                dico['name'] = partner.name if partner else "NA"
                dico['type'] = type

                operations_groupby_activity = [
                    (activity, [o for o in ope_ids]) for activity, ope_ids in groupby(
                        sorted(operations, key=lambda ope: ope.activity_id.id), lambda p: p.activity_id)]

                for operations_by_activity in operations_groupby_activity:
                    activity = operations_by_activity[0]
                    operations_ids = operations_by_activity[1]
                    activity_quantity = sum([o.quantity for o in operations_ids])

                    if form['action_number_opt'] == 'sup' and activity_quantity < form.get(
                            'action_number',
                            0):
                        continue
                    if form['action_number_opt'] == 'inf' and activity_quantity > form.get(
                            'action_number',
                            0):
                        continue

                    dico['tag'] = ", ".join(set([ope.tag_id.number if ope.tag_id else '' for ope in operations_ids]))
                    dico['infrastructure'] = ", ".join(set([ope.infrastructure_id.name if ope.infrastructure_id else ''
                                                            for ope in operations_ids]))
                    dico['activity'] = activity.name
                    dico['unit'] = activity.product_uom_id.name
                    dico['action_number'] = activity_quantity
                    partner_list.append(dico)
                    dico = {}
                    dico['name'] = " "
                    dico['type'] = " "

            else:
                if form['action_number_opt'] == 'sup' and len(operations) < form.get(
                        'action_number',
                        0):
                    continue
                if form['action_number_opt'] == 'inf' and len(operations) > form.get(
                        'action_number',
                        0):
                    continue

                dico['name'] = partner.name if partner else "NA"
                dico['type'] = partner.subscription_category_ids[0].name if partner.subscription_category_ids else "NA"
                dico['tag'] = ", ".join(set([ope.tag_id.number if ope.tag_id else '' for ope in operations]))
                dico['infrastructure'] = ", ".join(set([ope.infrastructure_id.name if ope.infrastructure_id else ''
                                                        for ope in operations]))
                dico['activity'] = operations[0].activity_id.name if operations else "NA"
                dico['unit'] = operations[0].activity_uom_id.name if operations else "NA"
                dico['action_number'] = len(operations)

                partner_list.append(dico)

        return partner_list, len(operations_set)

    def get_environment_operation_report_docargs(self, data, docids=False):
        """This method build the dict for the report.

        [{'doc_ids': documents ids,
          'doc_model': document model,
          'docs': infrastructure of the partner actions,
          'date_from': the start date of the action search,
          'date_to': the end date of the action search,
          'datas': data of partner (see construct_operation_report_datas method)
          'today': today's date,
          'filters': list of message to indicate filters used
        }]

        :param data: the parameters
        :param docids: docids
        :return: the dict
        """
        partner_list, nb_action = self.construct_operation_report_datas(data)

        # Additional parameters
        date_to = _("Undefined")
        form = data['form']

        if form.get('action_id', False):
            action_id = form['action_id'][0]
        else:
            action_id = self.env.ref('horanet_subscription.action_passage').id

        first_access = self.env['horanet.operation'].search([('action_id', '=', action_id)], order='time', limit=1)
        if first_access:
            date_from = datetime.strptime(first_access.time, "%Y-%m-%d %H:%M:%S").date().strftime('%d/%m/%Y')
        else:
            date_from = _("Undefined")
        if form.get('date_from', False):
            date_from = datetime.strptime(form['date_from'], DEFAULT_DATE_FORMAT).date().strftime('%d/%m/%Y')
        if form.get('date_to', False):
            date_to = datetime.strptime(form['date_to'], DEFAULT_DATE_FORMAT).date().strftime('%d/%m/%Y')

        today = datetime.strptime(fields.Date.today(), DEFAULT_DATE_FORMAT).date().strftime('%d/%m/%Y')

        filters_list = []
        if form.get('partner_category', False):
            ct = self.env['subscription.category.partner'].search([('id', 'in', form['partner_category'])])
            message = _("Partner type(s): ")
            filters_list.append(message + ', '.join(ct.mapped('name')))

        if form.get('action_id', False):
            message = _("Action: ")
            filters_list.append(message + unicode(form.get('action_id', False)[1]))
        else:
            message = _("Default action ")
            filters_list.append(message + unicode(self.env.ref('horanet_subscription.action_passage').name))

        if form.get('infrastructure_ids', False):
            infrastructures = self.env['horanet.infrastructure'].search(
                [('id', 'in', form['infrastructure_ids'])])
            message = _("Infrastructure(s): ")
            filters_list.append(message + ', '.join(infrastructures.mapped('name')))

        if form.get('activity_ids', False):
            infrastructures = self.env['horanet.activity'].search(
                [('id', 'in', form['activity_ids'])])
            message = _("Activities: ")
            filters_list.append(message + ', '.join(infrastructures.mapped('name')))

        if form.get('action_number_opt', False):
            if form['action_number_opt'] == 'sup':
                message = _("Action number superior to ")
                filters_list.append(message + unicode(form.get('action_number', False)))
            else:
                message = _("Action number inferior to ")
                filters_list.append(message + unicode(form.get('action_number', False)))

        return {
            'doc_ids': docids,
            'doc_model': 'horanet_operation',
            'docs': [],
            'date_from': date_from,
            'date_to': date_to,
            'datas': partner_list,
            'today': today,
            'filters': filters_list,
            'nb_action': nb_action if nb_action > 0 else None,
        }

    @api.model
    def render_html(self, docids, data=None):
        """We override this function to construct a dict for the report."""
        report_env = self.env['report']
        docargs = self.get_environment_operation_report_docargs(data=data, docids=docids)

        return report_env.render('environment_waste_collect.report_environment_operation', docargs)
