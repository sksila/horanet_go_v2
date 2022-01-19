# -*- coding: utf-8 -*-
from odoo import models, fields, api


class InheritedOperation(models.Model):
    # region Private attributes
    _inherit = 'horanet.operation'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    maintenance_equipment_id = fields.Many2one(string="Container", comodel_name='maintenance.equipment')
    chip_read = fields.Boolean(string="Is the chip read")
    equipment_allowed = fields.Boolean(string="Equipment allowed")
    equipment_emptied = fields.Boolean(string="Equipment emptied")
    equipment_broken = fields.Boolean(string="Equipment broken")
    sorting_problem = fields.Boolean(string="Sorting problem")
    size_exceeding = fields.Boolean(string="Size exceeding")
    production_point_id = fields.Many2one(
        string="Production point",
        comodel_name='production.point',
        compute='_compute_production_point_id',
    )
    # endregion

    # region Fields method
    @api.depends('maintenance_equipment_id')
    def _compute_production_point_id(self):
        """Get the production point at the time of the operation."""
        for rec in self:
            move = rec.maintenance_equipment_id and rec.maintenance_equipment_id.get_equipment_move(rec.time) or False
            rec.production_point_id = move and move.production_point_id or False
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    def get_operation_linked_packages(self, force_time=False):
        u"""Permet de retrouver les forfaits correspondant au paramétrage d'une opération."""
        self.ensure_one()
        search_time = force_time or self.time or self.env.context.get('force_time', fields.Datetime.now())

        if self.maintenance_equipment_id:
            packages = self.maintenance_equipment_id.get_equipment_linked_packages(search_time=search_time)
            log = u"\n\tResolve packages using Equipment(id:{equipment_id}) -> Move -> Subscription".format(
                equipment_id=str(self.maintenance_equipment_id.id))

            return packages, log

        return super(InheritedOperation, self).get_operation_linked_packages(force_time=force_time)

    # endregion
