# -*- coding: utf-8 -*-

from odoo import api, _
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


DEFAULT_DATE_FORMAT = '%Y-%m-%d'


class PickupXlsReport(ReportXlsx):
    """Class of environment partner xls report."""

    _name = 'report.environment_waste_collect.xlsx_report_pickup_request.xlsx'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        """We override this function to construct the xls report."""
        report_env = self.env['report.environment_waste_collect.report_pickup_request']
        docargs = report_env.get_pickup_request_report_docargs(data=data)

        datas = docargs['datas']
        date_from = docargs['date_from']
        date_to = docargs['date_to']
        total = docargs['total']

        # construct of the xls report (workbook)
        worksheet = workbook.add_worksheet()
        row = 0
        row_filtre = 6
        col_filtre = 8

        # Header construct
        header_format = workbook.add_format({'bold': True})
        header = [_("Service provider"), _("Waste"), _("Filling level (avg/min/max)"),
                  _("Pickup delay (avg/min/max)"), _("Pickup time (avg/min/max)"),
                  _("Quantity (avg/min/max)")]

        final_header = ["", _("Filling level (avg/min/max)"), _("Pickup delay (avg/min/max)"),
                        _("Pickup time (avg/min/max)"), _("Quantity (avg/min/max)")]

        # construct of tables
        for table in datas:
            col = 0

            for title in header:
                worksheet.write_string(row, col, title, header_format)
                col += 1
            row += 1

            # Data construct
            worksheet.add_table(row, 0, row + len(table['wastes']), len(header) - 1, {'header_row': False})

            if table['wastes']:
                for pickup in table['wastes']:
                    worksheet.write(row, 0, pickup['service_provider'])
                    worksheet.write(row, 1, pickup['name'])
                    worksheet.write(row, 2, "{avg}/{min}/{max}".format(
                                        avg=pickup['filling_level']['avg'],
                                        min=pickup['filling_level']['min'],
                                        max=pickup['filling_level']['max'],
                                    ))
                    worksheet.write(row, 3, "{avgl}:{avgr:02d}/{minl}:{minr:02d}/{maxl}:{maxr:02d}".format(
                                        avgl=int(pickup['pickup_delay']['avg']),
                                        avgr=int((pickup['pickup_delay']['avg'] * 60) % 60),
                                        minl=int(pickup['pickup_delay']['min']),
                                        minr=int((pickup['pickup_delay']['min'] * 60) % 60),
                                        maxl=int(pickup['pickup_delay']['max']),
                                        maxr=int((pickup['pickup_delay']['max'] * 60) % 60),
                                    ))
                    worksheet.write(row, 4, "{avgl}:{avgr:02d}/{minl}:{minr:02d}/{maxl}:{maxr:02d}".format(
                                        avgl=int(pickup['pickup_time']['avg']),
                                        avgr=int((pickup['pickup_time']['avg'] * 60) % 60),
                                        minl=int(pickup['pickup_time']['min']),
                                        minr=int((pickup['pickup_time']['min'] * 60) % 60),
                                        maxl=int(pickup['pickup_time']['max']),
                                        maxr=int((pickup['pickup_time']['max'] * 60) % 60),

                                    ))
                    worksheet.write(row, 5, "{avg}/{min}/{max}".format(
                                        avg=int(pickup['quantity']['avg']),
                                        min=int(pickup['quantity']['min']),
                                        max=int(pickup['quantity']['max']),
                                    ))

                    row += 1

                worksheet.write(row, 1, "Total")
                worksheet.write(row, 2, "{avg}/{min}/{max}".format(
                                    avg=int(table['total']['filling_level']['avg']),
                                    min=int(table['total']['filling_level']['min']),
                                    max=int(table['total']['filling_level']['max']),
                                ))
                worksheet.write(row, 3, "{avgl}:{avgr:02d}/{minl}:{minr:02d}/{maxl}:{maxr:02d}".format(
                                    avgl=int(table['total']['pickup_delay']['avg']),
                                    avgr=int((table['total']['pickup_delay']['avg'] * 60) % 60),
                                    minl=int(table['total']['pickup_delay']['min']),
                                    minr=int((table['total']['pickup_delay']['min'] * 60) % 60),
                                    maxl=int(table['total']['pickup_delay']['max']),
                                    maxr=int((table['total']['pickup_delay']['max'] * 60) % 60),
                                ))
                worksheet.write(row, 4, "{avgl}:{avgr:02d}/{minl}:{minr:02d}/{maxl}:{maxr:02d}".format(
                                    avgl=int(table['total']['pickup_time']['avg']),
                                    avgr=int((table['total']['pickup_time']['avg'] * 60) % 60),
                                    minl=int(table['total']['pickup_time']['min']),
                                    minr=int((table['total']['pickup_time']['min'] * 60) % 60),
                                    maxl=int(table['total']['pickup_time']['max']),
                                    maxr=int((table['total']['pickup_time']['max'] * 60) % 60),
                                ))
                worksheet.write(row, 5, "{avg}/{min}/{max}".format(
                                    avg=int(table['total']['quantity']['avg']),
                                    min=int(table['total']['quantity']['min']),
                                    max=int(table['total']['quantity']['max']),
                                ))
                row += 3

            else:
                worksheet.write(row, 0, "No data")

        if len(datas) > 1:
            # We construct a final table to resume pickups
            col = 1
            for title in final_header:
                worksheet.write_string(row, col, title, header_format)
                col += 1
            row += 1

            worksheet.add_table(row, 0, row + 1, len(final_header), {'header_row': False})

            worksheet.write(row, 1, "Total")
            worksheet.write(row, 2, "{avg}/{min}/{max}".format(
                                avg=int(total['filling_level']['avg']),
                                min=int(total['filling_level']['min']),
                                max=int(total['filling_level']['max']),
                            ))
            worksheet.write(row, 3, "{avgl}:{avgr:02d}/{minl}:{minr:02d}/{maxl}:{maxr:02d}".format(
                                avgl=int(total['pickup_delay']['avg']),
                                avgr=int((total['pickup_delay']['avg'] * 60) % 60),
                                minl=int(total['pickup_delay']['min']),
                                minr=int((total['pickup_delay']['min'] * 60) % 60),
                                maxl=int(total['pickup_delay']['max']),
                                maxr=int((total['pickup_delay']['max'] * 60) % 60),
                            ))

            worksheet.write(row, 4, "{avgl}:{avgr:02d}/{minl}:{minr:02d}/{maxl}:{maxr:02d}".format(
                                avgl=int(total['pickup_time']['avg']),
                                avgr=int((total['pickup_time']['avg'] * 60) % 60),
                                minl=int(total['pickup_time']['min']),
                                minr=int((total['pickup_time']['min'] * 60) % 60),
                                maxl=int(total['pickup_time']['max']),
                                maxr=int((total['pickup_time']['max'] * 60) % 60),
                            ))
            worksheet.write(row, 5, "{avg}/{min}/{max}".format(
                                avg=int(total['quantity']['avg']),
                                min=int(total['quantity']['min']),
                                max=int(total['quantity']['max']),
                            ))

        # Filter construct
        period = _("Period: {date_from} to {date_to}").format(date_from=date_from, date_to=date_to)
        worksheet.write(row_filtre - 2, col_filtre, period)
        worksheet.write(row_filtre, col_filtre, _("This report contains the following datas for each waste site and "
                                                  "each waste:"))
        worksheet.write(row_filtre + 1, col_filtre, _("The filling level (average, minimum and maximum) at the moment "
                                                      "of the pickup in %."))
        worksheet.write(row_filtre + 2, col_filtre, _("The pickup delay (average, minimum and maximum) in hour."))
        worksheet.write(row_filtre + 3, col_filtre, _("The pickup time (average, minimum and maximum) in hour."))
        worksheet.write(row_filtre + 4, col_filtre, _("The quantity (average, minimum and maximum) in m3."))


PickupXlsReport('report.environment_waste_collect.xlsx_report_pickup_request.xlsx', 'environment.pickup.request')
