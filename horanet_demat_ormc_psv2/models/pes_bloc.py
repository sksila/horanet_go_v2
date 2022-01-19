# -*- coding: utf-8 -*-

from odoo import models, fields


class PesBloc(models.Model):
    # region Private attributes
    _name = 'pes.bloc'
    _description = 'File Bloc'
    _order = "sequence, id"
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Char(string="Description")
    is_root = fields.Boolean(string="Root element")
    is_required = fields.Boolean(string="Required")
    namespace_id = fields.Many2one(
        string="Namespace",
        comodel_name='pes.bloc.attrs',
        domain="[('attrs_type','=','namespace')]")
    sequence = fields.Integer(string="Sequence", default=10)
    pes_domain_id = fields.Many2one(string="Domain", comodel_name='pes.domain')
    children_bloc_ids = fields.Many2many(
        string="Children Blocs",
        comodel_name='pes.bloc',
        relation='pes_bloc_parenty_rel',
        column1='parent_bloc',
        column2='child_bloc',
    )
    attrs_ids = fields.Many2many(
        string="Attributes",
        comodel_name='pes.bloc.attrs',
        relation='pes_bloc_attrs_rel',
        column1='bloc_id',
        column2='attrs_id',
    )

    conditionnal_attr_id = fields.Many2one(string="Conditionnal attribute", comodel_name='pes.bloc.attrs')

    pes_input_object_id = fields.Many2one(string="Input Object", comodel_name='pes.input.object')

    element_value_type = fields.Selection(
        string="Element value Type",
        selection=[('element', "Element"), ('text', "Text")],
        default='element',
    )
    field_type = fields.Selection(
        string="Text value Type",
        selection=[('text', "Text"), ('field', "Field"), ('function', "Function")],
    )
    value = fields.Text(string="Value")
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
