# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class HoranetVehicle(models.Model):
    """This class represent a model of vehicle."""

    # region Private attributes
    _name = 'partner.contact.identification.vehicle'
    _inherits = {'partner.contact.identification.medium': 'medium_id'}
    _inherit = ['mail.thread']
    _sql_constraints = [
        ('unicity_on_vehicle_identification_number', 'UNIQUE(vehicle_identification_number)',
         _("A vehicle with this vehicle identification number already exists.")),
        ('unicity_on_medium_id', 'UNIQUE(medium_id)',
         _("Medium_id must be unique."))
    ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    medium_id = fields.Many2one(
        string="Medium",
        comodel_name='partner.contact.identification.medium',
        required=True,
        ondelete='cascade',
    )

    display_name_vehicle = fields.Char(
        string="Name of the vehicule",
        compute='_compute_display_name_vehicule',
        store=False,
    )

    vehicle_identification_number = fields.Char(string="Vehicle Identification Number")

    brand = fields.Char(
        string="Vehicle brand",
    )

    vehicle_model_name = fields.Char(
        string="Vehicle model name",
    )

    color = fields.Char(
        string="Vehicle color",
    )

    ptac = fields.Integer(
        string="PTAC",
        help="F.2 of vehicle documentation",
        track_visibility='onchange',
    )

    documentation_id = fields.Many2one(
        string="Vehicle documentation",
        comodel_name='ir.attachment',
        domain="['&', "
               "('partner_id', '=', partner_id),"
               "('document_type_id.technical_name', '=', 'vehicle_registration_card')]",
        track_visibility='onchange'
    )

    vehicle_type_id = fields.Many2one(
        string="Vehicle type",
        comodel_name='partner.contact.identification.vehicle.type',
        help="J.1 of vehicle documentation",
        track_visibility='onchange',
    )

    license_plate_mapping = fields.Many2one(
        string="Mapping of license plate",
        comodel_name='partner.contact.identification.mapping',
        default=lambda self: self.env.ref('partner_identification_license_plate.immatriculation_mapping'),
        readonly=True,
    )

    license_plate = fields.Many2one(
        string="License plate",
        comodel_name='partner.contact.identification.tag',
        compute='_compute_license_plate',
        store=False,
    )

    # endregion

    # region Fields method
    @api.depends('tag_ids')
    def _compute_license_plate(self):
        """Compute the fields license plate."""
        immat_mapping = self.env.ref('partner_identification_license_plate.immatriculation_mapping')
        for rec in self:
            rec.license_plate = rec.tag_ids.filtered(lambda tag: tag.mapping_id == immat_mapping)

    @api.depends('color', 'tag_ids', 'license_plate')
    def _compute_display_name_vehicule(self):
        """Compute the name of the vehicle in the format 'immat - partner.name'."""
        for rec in self:
            name = u"{license_plate_number} - {partner_name}".format(
                license_plate_number=rec.license_plate.number,
                partner_name=rec.partner_id.name if rec.partner_id else "-")
            rec.display_name_vehicle = name

    # endregion

    # region Constraints and Onchange
    @api.onchange('vehicle_type_id')
    def _onchange_medium_type_id(self):
        """Define the vehicle (and medium) as a vehicle."""
        if not self.type_id:
            self.type_id = self.env.ref('partner_identification_license_plate.vehicle_medium_type')

    @api.onchange('tag_ids')
    def _check_vehicle_have_one_license_plate(self):
        """Check if the vehicle has just one license plate."""
        if self.type_id == self.env.ref('partner_identification_license_plate.vehicle_medium_type'):
            if len(self.tag_ids) > 1:
                raise exceptions.ValidationError(_("A vehicle has just one tag (one license plate)."))
            if self.tag_ids and self.tag_ids[0].mapping_id != \
                    self.env.ref('partner_identification_license_plate.immatriculation_mapping'):
                raise exceptions.ValidationError(_("The tag of a vehicle must be a license plate."))

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        u"""
        Surcharge du create pour lier la plaque d'immatriculation au medium que l'on vient de créer.

        Le medium étant crée suite à la création du véhicule.
        """
        new_vehicle = super(HoranetVehicle, self).create(vals)
        if new_vehicle.tag_ids:
            license_plate = new_vehicle.tag_ids.filtered(
                lambda tag:
                tag.mapping_id == self.env.ref('partner_identification_license_plate.immatriculation_mapping'))

            if license_plate:
                license_plate.medium_id = new_vehicle.medium_id

        return new_vehicle
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
