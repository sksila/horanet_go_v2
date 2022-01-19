# -*- coding: utf-8 -*-

import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)

COMMUNICATION_TYPE = [('tcp_ip', 'TCP/IP'), ('modem', 'MODEM')]


class HoranetTerminalBiosVersion(models.Model):
    """Bios version of a terminal."""

    # region Private attributes
    _name = 'tco.terminal.bios.version'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Number', required=True)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('name')
    def _check_name(self):
        """Check if the bios name is valid.

        :raise: odoo.exceptions.ValidationError if the field is empty
        """
        for rec in self:
            if len(rec.name.strip()) == 0:
                raise exceptions.ValidationError(_('Number cannot be empty'))

    # endregion

    # region CRUD (overrides)

    # endregion

    # region Actions
    def get_or_create(self, terminal_bios_version):
        """Get or create tco.terminal.bios.version record.

        :return: tco.terminal.bios.version
        """
        rec_terminal_bios_version = self.search(args=[('name', '=like', terminal_bios_version['name'])])
        if not rec_terminal_bios_version:
            _logger.debug("tco.terminal.bios.version identified by name ["
                          + terminal_bios_version['name']
                          + "] doesn't exists, create it!")
            rec_terminal_bios_version = self.create(terminal_bios_version)
        else:
            rec_terminal_bios_version.ensure_one()
        return rec_terminal_bios_version

    # endregion

    # region Model methods
    # endregion

    pass
