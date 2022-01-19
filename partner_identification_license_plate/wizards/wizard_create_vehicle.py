# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class WizardCreateVehicle(models.TransientModel):
    """Wizard to create vehicle."""

    # region Private attributes
    _name = 'wizard.create.vehicle'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    license_plate = fields.Char(string="License plate")
    ptac = fields.Integer(
        string="PTAC",
        help="F.2 of vehicle documentation",
    )
    vehicle_type_id = fields.Many2one(
        string="Vehicle type",
        comodel_name='partner.contact.identification.vehicle.type',
        help="J.1 of vehicle documentation",
    )
    assignation_start_date = fields.Datetime(
        string="Start date",
        default=fields.Datetime.now,
        required=True,
    )

    assignation_end_date = fields.Datetime(string="End date")

    documentation_id = fields.Many2one(
        string="Vehicle documentation",
        comodel_name='ir.attachment',
        domain="['&', "
               "('partner_id', '=', partner_id),"
               "('document_type_id.technical_name', '=', 'vehicle_registration_card')]"
    )

    license_plate_mapping = fields.Many2one(
        string="Mapping of license plate",
        comodel_name='partner.contact.identification.mapping',
        default=lambda self: self.env.ref('partner_identification_license_plate.immatriculation_mapping'),
        readonly=True,
    )

    partner_id = fields.Many2one(
        string="Partner",
        comodel_name='res.partner',
    )

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # # region Actions
    def create_vehicle_from_license_plate(self):
        """Action of vehicle creation."""
        assignation_model = self.env['partner.contact.identification.assignation']
        tag_model = self.env['partner.contact.identification.tag']
        mapping_id = self.env.ref('partner_identification_license_plate.immatriculation_mapping')

        # Recherche si l'immatriculation existe:
        existing_tag = tag_model.search([('number', '=', self.license_plate), ('mapping_id', '=', mapping_id.id)])

        if existing_tag:
            # recherche de l'assignation associé
            existing_assignations = assignation_model.search([('tag_id', '=', existing_tag.id)])

            if not existing_assignations:
                vehicle = self.env['partner.contact.identification.vehicle'].create({
                    'ptac': self.ptac,
                    'vehicle_type_id': self.vehicle_type_id.id,
                    'documentation_id': self.documentation_id.id,
                    'type_id': self.env.ref('partner_identification_license_plate.vehicle_medium_type').id,
                })

                existing_tag.medium_id = vehicle.medium_id.id
                # Creation de l'assignation
                assignation_model.create({
                    'start_date': self.assignation_start_date,
                    'end_date': self.assignation_end_date,
                    'tag_id': existing_tag.id,
                    'reference_id': '{model},{model_id}'.format(model="res.partner", model_id=self.partner_id.id),
                })
                return

            # on vérifie que l'on peut assigner cette immatriculation
            for existing_assignation in existing_assignations:
                if self.assignation_start_date < existing_assignation.start_date:
                    if self.assignation_end_date and \
                            (self.assignation_start_date < self.assignation_end_date < existing_assignation.start_date):
                        can_assign = True
                    else:
                        can_assign = False
                else:
                    if existing_assignation.end_date and self.assignation_start_date > existing_assignation.end_date:
                        can_assign = True
                    else:
                        can_assign = False

                if can_assign is False:
                    raise ValidationError(
                        _("This license plate already exist and is assigned to {vehicle_owner} for the {start_date} to "
                          "{end_date}").format(
                            vehicle_owner=existing_assignation.partner_id.name,
                            start_date=existing_assignation.start_date,
                            end_date=existing_assignation.end_date if existing_assignation.end_date else "---"
                        ))

            # On peut assigner l'immat
            assignation_model.create({
                'start_date': self.assignation_start_date,
                'end_date': self.assignation_end_date,
                'tag_id': existing_tag.id,
                'reference_id': '{model},{model_id}'.format(model="res.partner", model_id=self.partner_id.id),
            })

            # on vérifie qu'il y a bien un véhicule associé au tag
            existing_vehicle = self.env['partner.contact.identification.vehicle'].search([
                ('tag_ids', '=', self.license_plate)])
            if existing_vehicle:
                existing_vehicle.write({
                    'vehicle_type_id': self.vehicle_type_id.id,
                    'ptac': self.ptac,
                    'documentation_id': self.documentation_id.id
                })
            else:
                new_vehicle = self.env['partner.contact.identification.vehicle'].create({
                    'ptac': self.ptac,
                    'vehicle_type_id': self.vehicle_type_id.id,
                    'documentation_id': self.documentation_id.id,
                    'type_id': self.env.ref('partner_identification_license_plate.vehicle_medium_type').id,
                })
                existing_tag.medium_id = new_vehicle.medium_id.id

        else:
            # creation d'un nouveau vehicule
            vehicle = self.env['partner.contact.identification.vehicle'].create({
                'ptac': self.ptac,
                'vehicle_type_id': self.vehicle_type_id.id,
                'documentation_id': self.documentation_id.id,
                'type_id': self.env.ref('partner_identification_license_plate.vehicle_medium_type').id,
            })

            # Création de la plaque d'immatriculation
            tag = tag_model.create({
                'number': self.license_plate,
                'mapping_id': mapping_id.id,
                'medium_id': vehicle.medium_id.id,
            })
            # Creation de l'assignation
            assignation_model.create({
                'start_date': self.assignation_start_date,
                'end_date': self.assignation_end_date,
                'tag_id': tag.id,
                'reference_id': '{model},{model_id}'.format(model="res.partner", model_id=self.partner_id.id),
            })

    # endregion

    # region Model methods
    # endregion
