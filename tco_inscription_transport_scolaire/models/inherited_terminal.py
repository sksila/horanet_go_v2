# -*- coding: utf-8 -*-

import datetime
import grp
import logging
import os
import shutil

from odoo import api, models

WEBSERVER_USER = "www-data"

_logger = logging.getLogger(__name__)


class HoranetTerminal(models.Model):
    # region Private attributes
    _inherit = 'tco.terminal'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def lb7_generate_all_files(self):
        """Generate all necessary files by the LB7.

        This method is used by cron_action_generate_all_files and configure_action wizard action.

        Generate  :
        - 'liste_blanche_xx.csv file', including white list for a lb7 terminal.
        :return: error list (used by terminal_lb7_configure wizard)
        """
        errors = super(HoranetTerminal, self).lb7_generate_all_files()

        # Generate 'liste_blanche_xxx.csv' files
        errors += self.lb7_generate_white_list_file()

        return errors

    @api.multi
    def lb7_generate_white_list_file(self):
        """Generate white list from school inscriptions for a terminal in csv file ('liste_blanche_xx.csv').

        :return: error list (used by terminal_lb7_configure wizard)
        """
        errors = list()
        root_path = self._get_terminal_lb7_directory_path()
        self._check_lb7_directory(root_path)

        final_path = root_path + '/listes/'
        tmp_path = root_path + '/tmp/'

        for rec in self:
            _logger.info("Generate white list for lb7 terminal %s", rec.identification_number)

            if not rec.model or rec.model != 'lb7':
                error = "Invalid lb7 for terminal " + str(rec.identification_number)
                errors.append(error)
                _logger.warning(error)
                rec.create_log(name="White list generation from cron process", method="lb7_generate_white_list_file",
                               message=error, is_error=True)
                continue

            if not rec.is_active:
                error = "Terminal {} is not active".format(str(rec.identification_number))
                errors.append(error)
                _logger.warning(error)
                rec.create_log(name="White list generation from cron process", method="lb7_generate_white_list_file",
                               message=error, is_error=True)
                continue

            # School inscription list with valid status and date associated to a partner
            terminal_lines_recs = rec.vehicle_id.mapped('vehicle_assignment_ids').filtered('is_valid').mapped(
                'service_id.line_ids')

            current_date = datetime.datetime.now()
            inscription_recs = self.env['tco.inscription.transport.scolaire'].search([
                ('date_start', '<=', current_date),
                ('date_end', '>=', current_date),
                ('status', '=', 'validated'),
                ('badge_id', '!=', False),
                '|',
                ('line_forward_id', 'in', terminal_lines_recs.ids),
                ('line_backward_id', 'in', terminal_lines_recs.ids),
            ])

            if not inscription_recs:
                error = "Unfounded inscription for terminal {}".format(str(rec.identification_number))
                errors.append(error)
                _logger.warning(error)
                rec.create_log(name="White list generation from cron process", method="lb7_generate_white_list_file",
                               message=error, is_error=True)
                continue

            inscription_lines = []
            for inscription_rec in inscription_recs:
                partner_id = self._fill(inscription_rec.recipient_id.id, length=10, stopgap='0')
                default_line = '00000'
                line_0 = default_line
                line_1 = default_line

                if terminal_lines_recs.filtered(lambda x: x.id in [inscription_rec.line_forward_id.id]):
                    line_0 = inscription_rec.line_forward_id.name
                if terminal_lines_recs.filtered(lambda x: x.id in [inscription_rec.line_backward_id.id]):
                    line_1 = inscription_rec.line_backward_id.name

                card_h3 = '0000000000000000'
                card_serial_number = '0000000000'

                for tag_rec in inscription_rec.badge_id.tag_ids:
                    mapping = tag_rec.mapping_id.mapping
                    if mapping == 'h3':
                        card_h3 = self._fill(tag_rec.number, length=16, stopgap='0', mapping='h3')
                    elif mapping == 'csn':
                        card_serial_number = self._fill(tag_rec.number, length=10, stopgap='0')

                inscription_lines.append([
                    str(partner_id),
                    card_serial_number,
                    card_h3,
                    self._escape_for_lb7_terminal(inscription_rec.recipient_id.lastname),
                    self._escape_for_lb7_terminal(inscription_rec.recipient_id.firstname),
                    self._escape_for_lb7_terminal(line_0),
                    self._escape_for_lb7_terminal(line_1),
                    self._escape_for_lb7_terminal(default_line),
                    self._escape_for_lb7_terminal(default_line)
                ])

            # Write file
            filename = "liste_blanche_" + str(rec.identification_number) + ".csv"

            _logger.info("Writing %s line(s) in %s file...", str(len(inscription_lines)),
                         rec.identification_number)

            with open(tmp_path + filename, "w") as white_list_file:
                for inscription_line in inscription_lines:
                    white_list_file.writelines(';'.join(inscription_line) + ';\n')

            _logger.info("%s file is generated successfully!", final_path + filename)
            shutil.move(tmp_path + filename, final_path + filename)
            os.chown(final_path + filename, os.getuid(), grp.getgrnam(WEBSERVER_USER).gr_gid)

            _logger.info("Configuration white list for terminal %s ended successfully", rec.identification_number)

            rec.create_log(name="White list generation from cron process", method="lb7_generate_white_list_file",
                           message="White list files generation completed without errors")

        return errors

    # endregion

    # region Model methods
    @staticmethod
    def _fill(text, **kwargs):
        text = str(text)
        length = int(kwargs.get('length', 0))
        stopgap = str(kwargs.get('stopgap', '_'))
        position = 'before' if kwargs.get('position', 'before') == 'before' else 'after'
        mapping = kwargs.get('mapping')

        i = int(length - len(text))

        if mapping == 'h3' and len(text) == 20:
            return text[0:10] + text[14:20]
        elif i < 0:
            return text
        else:
            while i > 0:
                if position == 'before':
                    text = stopgap + text
                elif position == 'after':
                    text += stopgap
                i -= 1

        return text

    # endregion

    pass
