# -*- coding: utf-8 -*-

from odoo import api, models, _, exceptions, fields


class VehicleMedium(models.Model):
    """Extend partner.contact.identification.medium to add the notion of vehicle."""

    # region Private attributes
    _inherit = 'partner.contact.identification.medium'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    vehicle_id = fields.One2many(
        string="Vehicle",
        comodel_name='partner.contact.identification.vehicle',
        inverse_name='medium_id',
    )
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('tag_ids')
    def _check_vehicle_medium_has_one_tag(self):
        """Check if the medium with the type 'vehicle' has just one license plate."""
        if self.type_id == self.env.ref('partner_identification_license_plate.vehicle_medium_type'):
            if len(self.tag_ids) > 1:
                raise exceptions.ValidationError(_("A vehicle has just one tag (one license plate)."))
            if self.tag_ids and self.tag_ids[0].mapping_id != \
                    self.env.ref('partner_identification_license_plate.immatriculation_mapping'):
                raise exceptions.ValidationError(_("The tag of a vehicle must be a license plate."))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
