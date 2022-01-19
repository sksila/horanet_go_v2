# -*- coding: utf-8 -*-
from odoo import models, fields, api


class InheritedRequests(models.Model):
    # region Private attributes
    _inherit = 'maintenance.request'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    exchanged = fields.Boolean(string="Exchanged")
    intervention_type_ids = fields.Many2many(string="Intervention type", comodel_name='maintenance.intervention.type',
                                             domain="[('maintenance_type', '=', maintenance_type)]")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.onchange('equipment_id', 'maintenance_type')
    def _onchange_equipment_maintenance_type(self):
        """Compute the name of the maintenance request."""
        if self.equipment_id and self.maintenance_type:
            self.name = '%s, %s' % (self.equipment_id.name, self.maintenance_type)

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """We subscribe the owner of the equipment. We link the maintenance and the application."""
        context = self.env.context
        request = super(InheritedRequests, self).create(vals)
        if context.get('environment_application_id', False):
            application = self.env['website.application'].browse(context.get('environment_application_id'))
            application.maintenance_request_id = request.id
            if request.equipment_id:
                # On met le propriétaire en follower mais seulement pour les notes (subtype_id = 1)
                request.message_subscribe(partner_ids=[request.equipment_id.owner_partner_id.id], subtype_ids=[1])
        return request

    @api.multi
    def write(self, vals):
        """We unsubscribe the owner of the previous equipment and we subscribe the new one."""
        # Spécifique à l'environnement, d'où le contexte
        if self.env.context.get('equipment_environment', False):
            if vals.get('equipment_id', False):
                # On désinscrit l'ancien
                self.message_unsubscribe(partner_ids=[self.equipment_id.owner_partner_id.id])
                write = super(InheritedRequests, self).write(vals)
                # On inscrit le nouveau
                self.message_subscribe(partner_ids=[self.equipment_id.owner_partner_id.id], subtype_ids=[1])
                return write
        return super(InheritedRequests, self).write(vals)

    @api.multi
    def _track_subtype(self, init_values):
        """We send a mail to notify the owner. It's specific to this module so we check the context."""
        self.ensure_one()
        # Spécifique à l'environnement, d'où le contexte
        stage_new = self.env.ref('maintenance.stage_0')
        if 'stage_id' in init_values and self.stage_id != stage_new and \
                self.env.context.get('equipment_environment', False):
            template_id = self.env.ref('environment_equipment.email_maintenance_request_stage_changed')
            template_id.send_mail(self.id, force_send=True)
        if 'stage_id' in init_values and self.stage_id == stage_new and \
                self.env.context.get('equipment_environment', False):
            template_id = self.env.ref('environment_equipment.email_maintenance_request_stage_new')
            template_id.send_mail(self.id, force_send=True)
        return super(InheritedRequests, self)._track_subtype(init_values)
        # endregion

        # region Actions
        # endregion

        # region Model methods
        # endregion
