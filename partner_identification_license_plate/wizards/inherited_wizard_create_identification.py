# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InheritCreateIdentification(models.TransientModel):
    """Allow a user to read/write a medium."""

    # region Private attributes
    _inherit = 'create.identification'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    brand = fields.Char(
        string="Vehicle brand",
    )

    vehicle_model_name = fields.Char(
        string="Vehicle model",
    )

    color = fields.Char(
        string="Vehicle color",
    )

    ptac = fields.Integer(
        string="PTAC",
        help="F.2 of vehicle documentation",
    )

    documentation_id = fields.Many2one(
        string="Vehicle documentation",
        comodel_name='ir.attachment',
        domain="['&',"
               "('partner_id', '=', partner_id),"
               "('document_type_id.technical_name', '=', 'vehicle_registration_card')]"
    )

    vehicle_type_id = fields.Many2one(
        string="Vehicle type ",
        comodel_name='partner.contact.identification.vehicle.type',
        help="J.1 of vehicle documentation",
    )

    is_medium_type_vehicle = fields.Boolean(
        string="Is medium type vehicle",
        compute='_compute_is_vehicle',
    )

    vehicle_identification_number = fields.Char(string="Vehicle Identification Number")
    # endregion

    # region Fields method
    @api.depends('type_id')
    def _compute_is_vehicle(self):
        """Compute the field is_vehicle."""
        for rec in self:
            if rec.type_id == self.env.ref('partner_identification_license_plate.vehicle_medium_type'):
                rec.is_medium_type_vehicle = True
            else:
                rec.is_medium_type_vehicle = False
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    def create_vehicle(self, medium_type, tag_ids, brand=False, vehicle_model_name=False, color=False,
                       ptac=False, documentation_id=False, vehicle_type_id=False, vehicle_identification_number=False):
        """Create a vehicle for each license plate given.

        :param : medium_type: the type of the medium
        :param : brand: the brand of the vehicle
        :param : tag_ids: recordset of tag
        :param : vehicle_model_name: name of the vehicle model (ex: Laguna)
        :param : color: color of the vehicle
        :param : ptac: Ptac of the vehicle
        :param : documentation_id: record of the vehicle documentation
        :param : vehicle_type_id: type of the vehicle (ex: VP, CTTE)
        :param : vehicle_identification_number: the vehicle number (unique per vehicle)
        """
        licenses_plates = tag_ids.filtered(lambda tag:
                                           tag.mapping_id ==
                                           self.env.ref('partner_identification_license_plate.immatriculation_mapping'))

        for license_plate in licenses_plates:
            vehicle_model = self.env['partner.contact.identification.vehicle']
            medium = self.env['partner.contact.identification.medium'].search([
                ('tag_ids', 'in', licenses_plates.ids),
                ('type_id', '=', medium_type.id),
            ])

            vehicle_model.create({
                'medium_id': medium.id,
                'type_id': medium_type.id,
                'brand': brand,
                'vehicle_model_name': vehicle_model_name,
                'color': color,
                'ptac': ptac,
                'documentation_id': documentation_id.id,
                'vehicle_type_id': vehicle_type_id.id,
                'tag_ids': license_plate,
                'vehicle_identification_number': vehicle_identification_number,
            })
    # endregion

    # region Actions
    def action_create_medium(self):
        """Override of the action_create_medium to create a vehicule if medium_type is 'vehicle'."""
        super(InheritCreateIdentification, self).action_create_medium()
        if self.type_id == self.env.ref('partner_identification_license_plate.vehicle_medium_type'):
            self.create_vehicle(
                medium_type=self.type_id,
                brand=self.brand,
                vehicle_model_name=self.vehicle_model_name,
                color=self.color,
                ptac=self.ptac,
                documentation_id=self.documentation_id,
                vehicle_type_id=self.vehicle_type_id,
                tag_ids=self.tag_ids,
                vehicle_identification_number=self.vehicle_identification_number,
            )
    # endregion

    # region Model methods
    # endregion
