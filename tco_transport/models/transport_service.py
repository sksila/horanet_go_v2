# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models


class HoranetTransportService(models.Model):
    """A service is a group of lines."""

    # region Private attributes
    _name = 'tco.transport.service'
    _sql_constraints = [
        (
            'unicity_on_name',
            'UNIQUE(name)',
            _('A service with this name already exists.')
        )
    ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True, copy=False)

    line_ids = fields.One2many(
        string='Lines',
        comodel_name='tco.transport.line',
        inverse_name='service_id'
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
    # endregion

    # region Actions
    # endregion

    # region Model methods

    # endregion

    pass
