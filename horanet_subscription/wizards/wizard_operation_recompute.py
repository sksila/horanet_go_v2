# 1 : imports of python lib
import logging

from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class WizardOperationRecompute(models.TransientModel):
    # region Private attributes
    _name = 'wizard.operation.recompute'
    _description = "wizard to recompute multiple operation"
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    operation_ids = fields.Many2many(string="Operations to recompute",
                                     comodel_name='horanet.operation')

    package_line_ids = fields.Many2many(
        string="Package lines to recompute",
        comodel_name='horanet.package.line',
    )
    package_line_operation_ids = fields.Many2many(
        string="Operations to recompute",
        comodel_name='horanet.operation',
        compute='_compute_package_line_operation_ids'
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.onchange('package_line_ids')
    def _compute_package_line_operation_ids(self):
        if self.package_line_ids:
            self.package_line_operation_ids = self.package_line_ids.mapped(
                'usage_ids.origin_engine_result_id.trigger_operation_id')
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_multi_recompute(self):
        """Call the force recompute for each operation, ordered by time asc."""
        operations_to_recompute = self.operation_ids + self.package_line_operation_ids
        operations_to_recompute.sorted('time', reverse=False).action_force_recompute()
    # endregion
    pass
