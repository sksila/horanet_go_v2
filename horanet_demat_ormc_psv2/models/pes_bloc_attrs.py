# -*- coding: utf-8 -*-

from odoo import models, fields


class PesBlocAttrs(models.Model):
    # region Private attributes
    _name = 'pes.bloc.attrs'
    _description = 'Bloc Attribute'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    attrs_type = fields.Selection(
        string="Attribute type",
        selection=[('simple', "Simple"), ('namespace', "Namespace")],
    )
    description = fields.Char(string="Description")
    value_type = fields.Selection(
        string="Value Type",
        selection=[('simple', "Simple"), ('reference', "Reference")],
        default='simple',
    )
    field_type = fields.Selection(
        string="Field Type", selection=[('text', "Text"), ('field', "Field"), ('function', "Function")],
    )
    value = fields.Text(string="Value")
    reference_id = fields.Many2one(string="Referential", comodel_name='pes.referential')
    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
