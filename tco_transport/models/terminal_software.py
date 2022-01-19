# -*- coding: utf-8 -*-

import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class HoranetTerminalSoftware(models.Model):
    """Software used by the terminal."""

    # region Private attributes
    _name = 'tco.terminal.software'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)
    version_id = fields.Many2one(
        string='Version',
        comodel_name='tco.terminal.software.version',
        required=True
    )

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
                raise exceptions.ValidationError(_('Name cannot be empty'))

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
            name = '{} {}'.format(rec.name, rec.version_id.display_name)
            result.append((rec.id, name))

        return result

    # endregion

    # region Actions
    def get_or_create(self, terminal_software):
        """Get or create tco.terminal.software record.

        :return: tco.terminal.software
        """
        rec_terminal_software = self.search(
            args=[
                ('name', '=like', terminal_software['name']),
                ('version_id', '=', terminal_software['version_id']),
            ],
        )
        if not rec_terminal_software:
            _logger.debug("tco.terminal.software identified by name ["
                          + terminal_software['name']
                          + "] and version_id ["
                          + str(terminal_software['version_id'])
                          + "] doesn't exists, create it!")
            rec_terminal_software = self.create(terminal_software)
        else:
            rec_terminal_software.ensure_one()
        return rec_terminal_software

    # endregion

    # region Model methods
    # endregion

    pass
