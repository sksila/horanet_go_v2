# -*- coding: utf-8 -*-

import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class HoranetTerminalSoftwareVersion(models.Model):
    """Version of the software used in the terminal."""

    # region Private attributes
    _name = 'tco.terminal.software.version'
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
        """Check if the name is valid.

        :raise: odoo.exceptions.ValidationError if the field is empty
        """
        for rec in self:
            if len(rec.name.strip()) == 0:
                raise exceptions.ValidationError(_('Number cannot be empty'))

    # endregion

    # region CRUD (overrides)

    # endregion

    # region Actions
    def get_or_create(self, terminal_software_version):
        """Get or create tco.terminal.software.version record.

        :return: tco.terminal.software.version
        """
        rec_terminal_software_version = self.search(args=[('name', '=like', terminal_software_version['name'])])
        if not rec_terminal_software_version:
            _logger.debug("tco.terminal.software.version identified by name ["
                          + terminal_software_version['name']
                          + "] doesn't exists, create it!")
            rec_terminal_software_version = self.create(terminal_software_version)
        else:
            rec_terminal_software_version.ensure_one()
        return rec_terminal_software_version

    # endregion

    # region Model methods
    # endregion

    pass
