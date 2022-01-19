# -*- coding: utf-8 -*-
from odoo import models, fields


class InterventionTypes(models.Model):

    # region Private attributes
    _name = 'maintenance.intervention.type'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="name", required=True)
    maintenance_type = fields.Selection(string="Maintenance type",
                                        selection=[('corrective', 'Corrective'), ('preventive', 'Preventive')])
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
