# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Partner(models.Model):
    """Extend res.partner to add vehicle."""

    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    vehicle_ids = fields.Many2many(
        string="Vehicles",
        comodel_name='partner.contact.identification.vehicle',
        compute='_compute_vehicle_ids',
        store=False,
    )

    # endregion

    # region Fields method
    @api.depends('assignation_ids')
    def _compute_vehicle_ids(self):
        """Compute vehicules of the partner."""
        for rec in self:
            active_assignation = rec.assignation_ids.filtered('is_active')
            if rec.id and active_assignation:
                rec.vehicle_ids = rec.env['partner.contact.identification.vehicle'].search(
                    [('tag_ids', 'in', active_assignation.mapped('tag_id').ids)]).ids

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
