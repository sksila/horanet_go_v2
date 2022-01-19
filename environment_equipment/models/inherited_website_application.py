# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    """We add a field container."""

    # region Private attributes
    _inherit = 'website.application'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    container_id = fields.Many2one(
        string="Container",
        comodel_name='maintenance.equipment',
        compute='_compute_container_id',
        store=True,
    )
    maintenance_request_id = fields.Many2one(
        string="Maintenance request",
        comodel_name='maintenance.request',
    )

    # endregion

    # region Fields method
    @api.depends('applicant_partner_id')
    def _compute_container_id(self):
        """Get the container of the applicant user."""
        for rec in self:
            if rec.applicant_partner_id:
                # TODO Prendre en compte le fait que l'usager peut avoir plusieurs bacs
                # TODO  = le rajouter sur le modèle de téléservice
                equipments = rec.container_id.search([('owner_partner_id', '=', rec.applicant_partner_id.id)])
                rec.container_id = equipments and equipments[0].id or False
            else:
                rec.container_id = False

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_open_maintenance_request(self):
        """Open the maintenance request."""
        self.ensure_one()
        view = self.env.ref('environment_equipment.environment_maintenance_request_form_view')
        return {
            'name': 'Maintenance request',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'maintenance.request',
            'type': 'ir.actions.act_window',
            'view_id': view.id,
            'context': {'equipment_environment': True},
            'res_id': self.maintenance_request_id.id,
            'target': 'current',
        }

    # endregion

    # region Model methods
    # endregion

    pass
