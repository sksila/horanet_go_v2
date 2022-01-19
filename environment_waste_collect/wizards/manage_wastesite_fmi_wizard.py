
from odoo import api, fields, models, _, exceptions


class ManageWasteSiteFMI(models.TransientModel):
    """Wizard de gestion de la FMI des sites de collecte."""

    # region Private attributes
    _name = 'waste.site.fmi.wizard'

    # endregion

    # region Default methods
    @api.multi
    def _default_attendance(self):
        attendance = 0
        if self.env.context.get('default_waste_site_id', False):
            waste_site = self.waste_site_id.browse(self.env.context['default_waste_site_id'])
            if waste_site:
                attendance = waste_site.current_attendance
        return attendance

    # endregion

    # region Fields declaration
    waste_site_id = fields.Many2one(
        string="Waste Site",
        comodel_name='environment.waste.site',
        required=True)

    is_attendance_controlled = fields.Boolean(
        related='waste_site_id.is_attendance_controlled')
    attendance_threshold = fields.Integer(
        related='waste_site_id.attendance_threshold')
    current_attendance = fields.Integer(
        related='waste_site_id.current_attendance', )
    could_attend = fields.Boolean(
        related='waste_site_id.could_attend')
    attendance = fields.Integer(
        string="New attendance",
        default=_default_attendance)
    is_fmi_currently_controlled = fields.Boolean(
        string="Is attendance currently controlled",
        compute='compute_is_fmi_currently_controlled',
        store=False)

    # endregion

    # region Fields method
    @api.depends('waste_site_id')
    def compute_is_fmi_currently_controlled(self):
        for rec in self:
            rec.is_fmi_currently_controlled = rec.waste_site_id.is_fmi_control_enable()

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_validate(self):
        # Pseudo action du trigger validation and related fields saving
        pass

    @api.multi
    def action_calibrate_fmi(self):
        self.create_operation_fmi(calibrate=str(self.attendance))
        return

    @api.multi
    def action_disable_for_the_day(self):
        self.create_operation_fmi(disable=True)
        return

    @api.multi
    def action_enable_for_the_day(self):
        self.create_operation_fmi(enable=True)
        return

    # endregion

    # region Model methods
    @staticmethod
    def null_action():
        """Null action used to avoid closing the wizard."""
        return {
            "type": "set_scrollTop",
        }

    @api.model
    def create_operation_fmi(self, calibrate=False, disable=False, enable=False):
        """Create an operation with the current user as creator."""
        vals = {
            'create_uid': self.env.uid,
            'write_uid': self.env.uid,
            'disable_computation': True,
            'infrastructure_id': self.waste_site_id.infrastructure_id.id,
            'is_offline': False,
        }
        if calibrate:
            vals.update({
                'action_id': self.env.ref('horanet_subscription.action_calibrate_fmi').id,
                'quantity': int(calibrate)})
        elif disable:
            vals.update({
                'action_id': self.env.ref('horanet_subscription.action_disable_fmi').id})
        elif enable:
            vals.update({
                'action_id': self.env.ref('horanet_subscription.action_enable_fmi').id})

        if not vals.get('action_id', False):
            raise exceptions.ValidationError(_("Bad parameter, no action found"))

        return self.env['horanet.operation'].sudo().create(vals)

    # endregion

    pass
