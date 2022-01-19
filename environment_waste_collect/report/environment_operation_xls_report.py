# -*- coding: utf-8 -*-

from odoo import api, _
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class OperationXlsReport(ReportXlsx):
    """Class of environment operation xls report."""

    _name = 'report.environment_waste_collect.xlsx_report_environment_operation.xlsx'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        """We override this function to construct the xls report."""
        # Get data
        partner_report_env = self.env['report.environment_waste_collect.report_environment_operation']
        docargs = partner_report_env.get_environment_operation_report_docargs(data=data)

        partner_list = docargs['datas']
        date_from = docargs['date_from']
        date_to = docargs['date_to']
        filters_list = docargs['filters']
        nb_action = docargs['nb_action']

        # construct of the xls report (workbook)
        worksheet = workbook.add_worksheet()
        row = 0
        col = 0
        row_filtre = 8
        col_filtre = 9

        # Header construct
        header = [_("Name"), _("Profile"), _("Infrastructure"), _("Tag"), _("Activity"), _("Action number"),
                  _("Unit of measure")]
        header_format = workbook.add_format({'bold': True})

        for title in header:
            worksheet.write_string(row, col, title, header_format)
            col += 1
        row += 1

        # Data construct
        worksheet.add_table(row, 0, row + len(partner_list), len(header) - 1, {'header_row': False})

        if partner_list:
            for partner in partner_list:
                worksheet.write(row, 0, partner['name'])
                worksheet.write(row, 1, partner['type'])
                worksheet.write(row, 2, partner['infrastructure'])
                worksheet.write(row, 3, partner['tag'])
                worksheet.write(row, 4, partner['activity'])
                worksheet.write(row, 5, partner['action_number'])
                worksheet.write(row, 6, partner['unit'])
                row += 1
        else:
            worksheet.write(row, 0, "No data")

        # Filter construct
        period = _("Period: {date_from} to {date_to}").format(date_from=date_from, date_to=date_to)
        worksheet.write(row_filtre-2, col_filtre, period)
        for filtre in filters_list:
            worksheet.write(row_filtre, col_filtre, str(filtre))
            row_filtre += 1
        if nb_action:
            nb_action = _("Sum of actions: {nb_action}").format(nb_action=nb_action)
            worksheet.write(row_filtre+1, col_filtre, nb_action)
        workbook.close()


OperationXlsReport('report.environment_waste_collect.xlsx_report_environment_operation.xlsx', 'horanet.operation')
