# -*- coding: utf-8 -*-

import csv
import grp
import logging
import os
import re
import shutil
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo.addons.horanet_web.tools.time import float_time_to_str

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import Warning, MissingError

_logger = logging.getLogger(__name__)

COMMUNICATION_TYPE = [('tcp_ip', 'TCP/IP'), ('modem', 'MODEM')]
TERMINAL_MODELS = [('lb7', 'LB7')]
LB7_STATUS_KEYS = [
    'DATE', 'TIME', 'SERVICE', 'LAST_CONNECT', 'UCLINUX', 'APPLI_NAME', 'APPLI_VER_CUR', 'IP_ADDR', 'MAC_ADDR']
WEBSERVER_USER = "www-data"


class HoranetTerminal(models.Model):
    """A terminal is a device placed in a vehicle to track people who get in the vehicle."""

    # region Private attributes
    _name = 'tco.terminal'
    _sql_constraints = [
        (
            'unicity_on_serial_number',
            'UNIQUE(serial_number)',
            _('A terminal with this serial number already exists.')
        )
    ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    identification_number = fields.Integer(
        string='Identification number', required=True
    )
    model = fields.Selection(string='Model', selection=TERMINAL_MODELS)
    software_id = fields.Many2one(
        string='Software',
        comodel_name='tco.terminal.software',
        required=True
    )
    bios_version_id = fields.Many2one(
        string='Bios version',
        comodel_name='tco.terminal.bios.version',
        required=True
    )
    serial_number = fields.Char(string='Serial number', required=True)

    is_active = fields.Boolean(string='Is active', default=True)
    last_synchronisation_date = fields.Datetime(string='Last synchronisation')
    last_configuration_date = fields.Datetime(string='Last configuration')
    terminal_time = fields.Datetime(string='Terminal time')
    dns_name = fields.Char(string='DNS name')
    ip_address = fields.Char(string='IP address')
    mac_address = fields.Char(string='Mac address')
    port_number = fields.Integer(string='Port number')
    communication_type = fields.Selection(
        string='Communication type', selection=COMMUNICATION_TYPE
    )
    vehicle_id = fields.Many2one(
        string='Vehicle',
        comodel_name='tco.transport.vehicle'
    )
    license_plate = fields.Char(
        string='Vehicle',
        related='vehicle_id.license_plate'
    )
    company_owner_id = fields.Many2one(
        string='Company owner',
        comodel_name='res.company'
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('identification_number')
    def _check_identification_number(self):
        """Check if the identification number is valid.

        :raise: odoo.exceptions.ValidationError if the field is equal to 0
        """
        for rec in self:
            if rec.identification_number == 0:
                raise exceptions.ValidationError(
                    _('Identification number cannot be equal to 0')
                )

    @api.constrains('serial_number')
    def _check_serial_number(self):
        """Check if the serial number is valid."""
        for rec in self:
            if len(rec.serial_number.strip()) == 0:
                raise exceptions.ValidationError(
                    _('Serial number cannot be empty')
                )

    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        """Compute for each record the name that will be displayed.

        :return: list of names for each records
        :rtype: [(int, str)]
        """
        result = []

        for rec in self:
            result.append((rec.id, '{} {}'.format(rec.identification_number,
                                                  rec.serial_number)))

        return result

    # endregion

    # region Actions
    @api.multi
    def create_log(self, **kwargs):
        self.ensure_one()

        if not kwargs.get('name'):
            raise MissingError("Missing name argument for create_log method")

        if not kwargs.get('method'):
            raise MissingError("Missing method argument for create_log method")

        self.env['tco.terminal.lb7.log'].create({
            'name': kwargs.get('name'),
            'method': kwargs.get('method'),
            'message': kwargs.get('message', ""),
            'is_error': kwargs.get('is_error', False),
            'model_id': self.env['ir.model'].search(args=[('model', '=', 'tco.terminal')]).id,
            'res_id': self.id,
            'user_id': self.env.user.id,
            'log_type': 'full',
        })

    @api.multi
    def lb7_generate_lines_file(self):
        """Generate csv file ligne_bus_habituelle_xx.csv.

        :return: error list (used by terminal_lb7_configure wizard)
        """
        errors = list()
        root_path = self._get_terminal_lb7_directory_path()
        self._check_lb7_directory(root_path)

        final_path = root_path + '/listes/'
        tmp_path = root_path + '/tmp/'

        for rec in self:
            _logger.info("Generate lines file for the terminal %s", rec.identification_number)

            # Check some terminal properties
            if not rec.is_active:
                error = "Terminal " + str(rec.identification_number) + " disabled"
                errors.append(error)
                _logger.warning(error)
                rec.create_log(
                    name="Files generation from cron process",
                    method="lb7_generate_lines_file",
                    message=error,
                    is_error=True)
                continue

            if not rec.model or rec.model != 'lb7':
                error = "Terminal " + str(rec.identification_number) + " is not lb7"
                errors.append(error)
                _logger.warning(error)
                rec.create_log(
                    name="Files generation from cron process",
                    method="lb7_generate_lines_file",
                    message=error,
                    is_error=True)
                continue

            if rec.vehicle_id.id is False:
                error = "No vehicle for terminal " + str(rec.identification_number)
                errors.append(error)
                _logger.warning(error)
                rec.create_log(
                    name="Files generation from cron process",
                    method="lb7_generate_lines_file",
                    message=error,
                    is_error=True)
                continue

            elif rec.vehicle_id.vehicle_assignment_ids is False or len(rec.vehicle_id.vehicle_assignment_ids) == 0:
                error = "No service for vehicle " + str(rec.vehicle_id.id)
                errors.append(error)
                _logger.warning(error)
                rec.create_log(
                    name="Files generation from cron process",
                    method="lb7_generate_lines_file",
                    message=error,
                    is_error=True)
                continue

            # Get vehicle lines associated with the terminal
            lines_of_vehicle = rec.vehicle_id.mapped('vehicle_assignment_ids').filtered('is_valid').mapped(
                'service_id.line_ids')

            if lines_of_vehicle is False or len(lines_of_vehicle) < 0:
                error = "No lines for vehicle " + str(rec.vehicle_id.id) + " with terminal " + str(
                    rec.identification_number)
                errors.append(error)
                _logger.warning(error)
                rec.create_log(
                    name="Files generation from cron process",
                    method="lb7_generate_lines_file",
                    message=error,
                    is_error=True)
                continue

            filename = "ligne_bus_habituelle_" + str(rec.identification_number) + ".csv"

            with open(tmp_path + filename, "w") as line_files:
                for rec_line in lines_of_vehicle:
                    line_files.writelines(";".join([
                        self._escape_for_lb7_terminal(rec_line.display_name),
                        rec_line.line_type == 'return' and '2' or '1',
                        float_time_to_str(rec_line.departure_time, '00:01'),
                        float_time_to_str(rec_line.arrival_time, '23:59')
                    ]) + ";\n")

            # Move file to final directory
            shutil.move(tmp_path + filename, final_path + filename)
            os.chown(final_path + filename, os.getuid(), grp.getgrnam(WEBSERVER_USER).gr_gid)

            # Update configuration date
            rec.write({'last_configuration_date': fields.Datetime.now()})

            _logger.info("%s file is generated successfully", final_path + filename)
            _logger.info("Configuration terminal %s ended successfully", rec.identification_number)

            rec.create_log(name="Files generation from cron process", method="lb7_generate_lines_file",
                           message="Transport lines files generation completed without errors")

        return errors

    @api.model
    def lb7_generate_vehicle_list_file(self):
        u"""Generate csv file liste_bus.csv.

        :return: error list (used by terminal_lb7_configure wizard)
        TRANSPORTEUR - IMMATRICULATION - SERVICE - N°VALIDEUR;
        """
        _logger.info("Generate all vehicles list for lb7 terminals")
        errors = list()

        root_path = self._get_terminal_lb7_directory_path()
        self._check_lb7_directory(root_path)

        final_path = root_path + '/listes/'
        tmp_path = root_path + '/tmp/'
        filename = 'liste_bus.csv'

        # Search for services list with a vehicle equipped with lb7 terminal
        vehicles = self.search([('model', '=', 'lb7')]).mapped('vehicle_id')

        # Search for transport lines into services
        vehicle_lines = list()
        for vehicle in vehicles:
            for terminal in vehicle.terminal_ids:
                for service in vehicle.vehicle_assignment_ids.filtered('is_valid').mapped('service_id'):
                    vehicle_lines.append([
                        self._escape_for_lb7_terminal(vehicle.owner_id.display_name),
                        self._escape_for_lb7_terminal(vehicle.license_plate),
                        self._escape_for_lb7_terminal(service.name),
                        str(terminal.identification_number),
                    ])

        # Write file
        _logger.debug("Writing {} line(s) in {} file.".format(str(len(vehicle_lines)), filename))

        with open(tmp_path + filename, "w") as fs_file:
            for vehicle_line in vehicle_lines:
                fs_file.writelines(';'.join(vehicle_line) + ';\n')

        # Move file into final directory
        _logger.debug("Moving liste_bus.csv file to {}.".format(final_path))
        shutil.move(tmp_path + filename, final_path + filename)
        os.chown(final_path + filename, os.getuid(), grp.getgrnam(WEBSERVER_USER).gr_gid)

        _logger.debug("Generate all vehicle lines for lb7 terminals ended successfully")

        self.env['tco.terminal.lb7.log'].create({
            'name': "Files generation from cron process",
            'method': "lb7_generate_vehicle_list_file",
            'message': "Vehicle list file generation completed without errors",
            'is_error': False,
            'model_id': self.env['ir.model'].search(args=[('model', '=', 'tco.terminal')]).id,
            'user_id': self.env.user.id,
            'log_type': 'full',
        })

        return errors

    @api.model
    def lb7_generate_all_service_line_file(self):
        """Generate csv file ligne_bus_total.csv.

        :return: error list (used by terminal_lb7_configure wizard)
        """
        _logger.info("Generate all services and lines for lb7 terminals")
        errors = list()

        root_path = self._get_terminal_lb7_directory_path()
        self._check_lb7_directory(root_path)

        final_path = root_path + '/listes/'
        tmp_path = root_path + '/tmp/'
        filename = 'ligne_bus_total.csv'

        # Search for services list with a vehicle equiped with lb7 terminal
        service_recs = self.search([('model', '=', 'lb7')]) \
            .mapped('vehicle_id.vehicle_assignment_ids') \
            .filtered('is_valid').mapped('service_id')

        # Search for transport lines into services
        current_services_lines = []
        for service_rec in service_recs:
            for line_rec in service_rec.line_ids:
                current_services_lines.append([
                    self._escape_for_lb7_terminal(service_rec.name),
                    self._escape_for_lb7_terminal(line_rec.display_name),
                    line_rec.line_type == 'return' and '2' or '1',
                    float_time_to_str(line_rec.departure_time, '00:00'),
                    float_time_to_str(line_rec.arrival_time, '23:59')
                ])

        # Write file
        _logger.debug("Writing %s line(s) in %s file.", str(len(current_services_lines)), filename)

        with open(tmp_path + filename, "w") as fs_file:
            for dic_rec in current_services_lines:
                fs_file.writelines(';'.join(dic_rec) + ';\n')

        # Move file into final directory
        _logger.debug("Moving ligne_bus_total.csv file to %s.", final_path)
        shutil.move(tmp_path + filename, final_path + filename)
        os.chown(final_path + filename, os.getuid(), grp.getgrnam(WEBSERVER_USER).gr_gid)

        _logger.debug("Generate all services and lines for lb7 terminals ended successfully")

        self.env['tco.terminal.lb7.log'].create({
            'name': "Files generation from cron process",
            'method': "lb7_generate_all_service_line_file",
            'message': "Transport for all services lines files generation completed without errors",
            'is_error': False,
            'model_id': self.env['ir.model'].search(args=[('model', '=', 'tco.terminal')]).id,
            'user_id': self.env.user.id,
            'log_type': 'full',
        })

        return errors

    @api.multi
    def lb7_generate_all_files(self):
        """Configure all active lb7 terminals.

        Generate :
        - 'ligne_bus_habituelle_xx.csv' file, including available lines for a lb7 terminal,
        - 'ligne_bus_total.csv file', including all services and lines for lb7 terminals.
        :return: error list (used by terminal_lb7_configure wizard)
        """
        _logger.info("Generate all files for lb7 terminals")
        errors = list()

        # Generate files
        errors += self.lb7_generate_lines_file()
        errors += self.lb7_generate_all_service_line_file()
        errors += self.lb7_generate_vehicle_list_file()

        _logger.info("Configure all active lb7 terminals ended successfully")
        return errors

    @api.model
    def cron_action_lb7_generate_all_files(self):
        """Configure all active lb7 terminals.

        Generate :
        - 'ligne_bus_habituelle_xx.csv' file, including available lines for a lb7 terminal,
        - 'ligne_bus_total.csv file', including all services and lines for lb7 terminals.
        :return: error list (used by terminal_lb7_configure wizard)
        """
        _logger.debug("Cron method cron_action_lb7_generate_all_files called")
        errors = list()

        # Search for active LB7 terminals and generate files
        terminal_recs = self.search([('model', '=', 'lb7'), ('is_active', '=', True)])
        errors += terminal_recs.lb7_generate_all_files()

        _logger.debug("Cron method cron_action_lb7_generate_all_files terminated")
        return errors

    @api.model
    def cron_action_lb7_record_moves(self):
        """Read lb7 moves files.

        Files are sent by terminal in 'pointages' directory.
        After process, they are archived into sub-directory 'archives'.
        :return: error list (used by terminal_lb7_configure wizard)
        """
        _logger.debug("Cron method cron_action_lb7_record_moves called")
        _logger.info("Get all moves lb7 files")
        errors = list()

        root_path = self._get_terminal_lb7_directory_path()
        self._check_lb7_directory(root_path)

        pointages_path = root_path + '/pointages/'
        pointages_csv_files = [f for f in os.listdir(pointages_path)
                               if os.path.isfile(os.path.join(pointages_path, f))
                               and os.path.splitext(f)[1].upper() == '.CSV']

        for pointages_csv_file in pointages_csv_files:
            errors_in_current_file = list()
            with open(pointages_path + pointages_csv_file, 'r') as pointages_csv:
                pointages_reader = csv.reader(pointages_csv, delimiter=";")
                for pointage in pointages_reader:

                    # Get pointage information from CSV file
                    csv_terminal_id = pointage[0]
                    csv_transaction_number = pointage[1]

                    csv_date_time = fields.Datetime.to_string(datetime.strptime(
                        pointage[2].split('-')[0] + pointage[3],
                        '%d/%m/%Y%H:%M:%S'
                    ))
                    csv_csn = self._convert_csn(pointage[4])
                    csv_h3 = self._convert_h3(pointage[5])
                    csv_line_name = pointage[6]
                    csv_status = pointage[7]

                    # Get the transport terminal record if exists, log an error if not exists
                    rec_terminal = self.search(
                        args=[
                            ('model', '=', 'lb7'),
                            ('identification_number', '=', csv_terminal_id)
                        ],
                        limit=1,
                    )

                    if len(rec_terminal) == 0:
                        error = "Terminal identified by id {} doesn't exists - line {}".format(
                            str(csv_terminal_id),
                            str(pointages_reader.line_num)
                        )
                        errors_in_current_file.append(error)
                        _logger.error(error)
                        continue

                    # Get the transport line record if exists
                    # Check line name from csv file terminal with escaped line name from database
                    # Bad performance are expected
                    line_rec = False
                    for line_rec_iter in self.env['tco.transport.line'].search(args=[]):
                        if self._escape_for_lb7_terminal(line_rec_iter.name) == csv_line_name:
                            line_rec = line_rec_iter

                    # Get the tag record if exists
                    tag_rec = self.env['partner.contact.identification.tag'].search(
                        args=['|', ('number', '=', csv_csn), ('number', '=', csv_h3)],
                        limit=1,
                    )

                    pointage_time = fields.Datetime.from_string(csv_date_time)

                    lb7_time_offset = int(self.env['horanet.transport.config'].get_lb7_time_offset())

                    pointage_time = pointage_time - relativedelta(hours=lb7_time_offset / 3600)

                    pointage_dict = {
                        'terminal_id': rec_terminal.id,
                        'transaction_number': csv_transaction_number,
                        'date_time': fields.Datetime.to_string(pointage_time),
                        'status': csv_status,
                        'vehicle_id': rec_terminal.vehicle_id and rec_terminal.vehicle_id.id,
                        'line_id': line_rec and line_rec.id,
                        'tag_id': tag_rec and tag_rec.id,
                        'partner_id': tag_rec.partner_id.id if tag_rec and tag_rec.partner_id else False
                    }

                    if self.env['tco.transport.pointage'].check_exists(pointage_dict):
                        error = "Pointage from terminal {} with transaction number {} " \
                                "at {} already exists - line {}".format(str(csv_terminal_id),
                                                                        str(csv_transaction_number),
                                                                        csv_date_time,
                                                                        str(pointages_reader.line_num))
                        errors_in_current_file.append(error)
                        _logger.error(error)
                        continue

                    self.env['tco.transport.pointage'].create(pointage_dict)

            message = "File \"{}\": ".format(pointages_csv_file)
            message += "\n".join(errors_in_current_file) if len(
                errors_in_current_file) > 0 else "Moves successfully retrieved"
            is_error = True if len(errors_in_current_file) > 0 else False

            self.env['tco.terminal.lb7.log'].create({
                'name': "Get pointages from cron process",
                'method': "cron_action_lb7_record_moves",
                'message': message,
                'is_error': is_error,
                'model_id': self.env['ir.model'].search(args=[('model', '=', 'tco.terminal')]).id,
                'user_id': self.env.user.id,
                'log_type': 'full',
            })

            # Archive current file
            shutil.move(pointages_path + pointages_csv_file, pointages_path + '/archives/' + pointages_csv_file)
            _logger.info("Successfully processed file ({}).".format(pointages_csv_file))
            errors += errors_in_current_file

        return errors

    @api.model
    def cron_action_lb7_record_status(self):
        """Read lb7 status files.

        Files are sent by terminal in 'Statuts' directory.
        After process, they are archived into sub-directory 'archives'.
        'ip_address', 'mac_address','terminal_time','bios_version_id','software_id' are updated on terminal.
        :return: error list (used by terminal_lb7_configure wizard)
        """
        _logger.debug("Cron method cron_action_lb7_record_status called")
        _logger.info("Get all status lb7 files")
        errors = list()

        root_path = self._get_terminal_lb7_directory_path()
        self._check_lb7_directory(root_path)

        status_path = root_path + '/Statuts/'
        status_csv_files = [f for f in os.listdir(status_path)
                            if os.path.isfile(os.path.join(status_path, f))
                            and os.path.splitext(f)[1].upper() == '.CSV']

        for status_csv_file in status_csv_files:
            errors_in_current_file = list()
            with open(status_path + status_csv_file, 'r') as status_csv:
                status_reader = csv.reader(status_csv, delimiter=";")
                terminal_ext_id = os.path.splitext(status_csv_file)[0].split("-")[1]

                # Search for lb7 terminals identified by identification number
                terminal_rec = self.search([
                    ('model', '=', 'lb7'),
                    ('identification_number', '=', terminal_ext_id)
                ])

                infos = dict()
                for line in status_reader:
                    key, val = line[0].split("=")
                    infos[key] = val.replace('\n', '')

                if len(terminal_rec) == 0:
                    error = "External id {} undefined for lb7 terminal".format(str(terminal_ext_id))
                    errors_in_current_file.append(error)
                    _logger.error(error)
                elif len(terminal_rec) > 1:
                    error = "Multiple lb7 terminal found with the same external id {}".format(str(terminal_ext_id))
                    errors_in_current_file.append(error)
                    _logger.error(error)
                elif not (all([k in infos.keys() for k in LB7_STATUS_KEYS]) and all(infos.values())):
                    error = "LB7 status information missing in {} file".format(status_path + status_csv_file)
                    errors_in_current_file.append(error)
                    _logger.error(error)
                else:
                    # Terminal bios version management
                    bios_rec = self.env['tco.terminal.bios.version'].get_or_create({'name': infos['UCLINUX']})

                    # Terminal software version management
                    version_rec = self.env['tco.terminal.software.version'].get_or_create(
                        {'name': infos['APPLI_VER_CUR']})

                    # Terminal software management
                    appli_rec = self.env['tco.terminal.software'].get_or_create(
                        {'name': infos['APPLI_NAME'], 'version_id': version_rec.id})

                    terminal_time = fields.Datetime.to_string(datetime.strptime(
                        infos['DATE'].split('-')[0] + infos['TIME'],
                        '%d/%m/%Y%H:%M:%S'
                    ))

                    # Refresh terminal data
                    terminal_rec.write({
                        'last_synchronisation_date': fields.Datetime.now(),
                        'ip_address': infos['IP_ADDR'],
                        'mac_address': infos['MAC_ADDR'],
                        'terminal_time': terminal_time,
                        'bios_version_id': bios_rec.id,
                        'software_id': appli_rec.id
                    })

            message = "File \"{}\": ".format(status_csv_file)
            message += "\n".join(errors_in_current_file) if len(
                errors_in_current_file) > 0 else "Status successfully retrieved"
            is_error = True if len(errors_in_current_file) > 0 else False

            self.env['tco.terminal.lb7.log'].create({
                'name': "Get terminal information from cron process",
                'method': "cron_action_lb7_record_status",
                'message': message,
                'is_error': is_error,
                'model_id': self.env['ir.model'].search(args=[('model', '=', 'tco.terminal')]).id,
                'user_id': self.env.user.id,
                'log_type': 'full',
            })

            # Archive current file
            shutil.move(status_path + status_csv_file, status_path + '/archives/' + status_csv_file)
            _logger.info("Successfully processed file ({}).".format(status_csv_file))
            errors += errors_in_current_file

        return errors

    # endregion

    # region Model methods
    @api.model
    def _get_terminal_lb7_directory_path(self):
        """Return the directory path where are stored files from terminals."""
        return self.env['ir.config_parameter'].get_param('tco_transport.terminal_lb7_directory_path')

    @staticmethod
    def _check_lb7_directory(root_path):
        """Check directory tree coherence of LB7 terminals."""
        list_folder = ['tmp',
                       'listes',
                       'ActionsOperateurs',
                       'download',
                       'upload',
                       'pointages',
                       'pointages/archives',
                       'Statuts',
                       'Statuts/archives']

        # Create root folder if not exists
        if not os.path.isdir(root_path):
            os.mkdir(root_path)
            os.chown(root_path, os.getuid(), grp.getgrnam(WEBSERVER_USER).gr_gid)
            _logger.info('Make root directory {}'.format(root_path))

        for folder_path in [root_path + '/' + folder_name for folder_name in list_folder]:
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
                os.chown(folder_path, os.getuid(), grp.getgrnam(WEBSERVER_USER).gr_gid)
                _logger.debug('Make directory {folder_path}'.format(folder_path=folder_path))

    @staticmethod
    def _convert_csn(csn):
        """Convert CSN from hexadecimal separated by period to decimal.

        :param csn: value of CSN
        :return converted value of CSN
        """
        if not re.search('([0-9A-Fa-f]{2}\.){3}[0-9A-Fa-f]{2}', csn):
            raise Warning(csn + "is not an hexadecimal value for a valid csv CSN")

        return csn.replace(".", "")

    @staticmethod
    def _convert_h3(h3):
        """Convert H3 from hexadecimal separated by period to hexadecimal without period.

        :param h3: value of H3
        :return converted value of H3
        """
        if not re.search('([0-9A-Fa-f]{2}\.){7}[0-9A-Fa-f]{2}', h3):
            raise Warning(h3 + "is not an hexadecimal value for a valid csv H3")

        h3 = h3.replace(".", "")
        h3 = h3[0:10] + '0000' + h3[10:16]
        return h3

    @staticmethod
    def _escape_for_lb7_terminal(text):
        pattern = re.compile('[\W_]+')
        return pattern.sub('', text)

    # endregion

    pass
