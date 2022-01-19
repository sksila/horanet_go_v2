# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EquipmentSetUpPartner(models.TransientModel):
    u"""Wizard assistant de création de partner environnement."""

    # region Private attributes
    _inherit = 'partner.setup.wizard'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    partner_equipment_ids = fields.Many2many(
        string="Partner equipments",
        comodel_name='maintenance.equipment',
        related='partner_id.active_equipment_allocations_ids',
        store=False,
    )
    active_move_equipment_ids = fields.Many2many(
        string="Partner move equipments",
        comodel_name='maintenance.equipment',
        compute='_compute_active_move_equipment_ids',
        store=False,
    )
    equipment_category_id = fields.Many2one(string="Equipment category", comodel_name='maintenance.equipment.category')
    chip_number = fields.Char(string="Chip number")
    tub_number = fields.Char(string="Tub number")

    equipment_id = fields.Many2one(string="Equipment",
                                   comodel_name='maintenance.equipment',
                                   domain="[('tub_number', '=?', tub_number),"
                                          " ('chip_number', '=?', chip_number),"
                                          " ('category_id', '=?', equipment_category_id),"
                                          " '|',"
                                          " ('allocation_ids', '=', False),"
                                          " ('allocation_ids.is_active', '=', False),"
                                          " ]",
                                   )

    has_active_stay_equipment = fields.Boolean(
        string="Has active stay equipment",
        compute='_compute_equipment_stay_in_production_point',
    )
    equipment_stay_in_production_point = fields.Many2many(
        string="Some equipments are related to the production point",
        comodel_name='partner.move.equipment.rel',
        compute='_compute_equipment_stay_in_production_point',
    )

    attribution_stay_equipment = fields.Many2many(
        string="Select equipments that are related to the production point",
        comodel_name='partner.move.equipment.rel',
        domain="[('move_id.production_point_id', '=', new_production_point_id),"
               " ('category_id.equipment_follows_producer', '=', False),"
               "('is_active', '=', True),"
               "('end_date', '=', False),"
               " '|',"
               " ('move_id.is_active', '=', False), "
               " ('move_id.end_date', '<', default_new_situation_date),"
               "]"
    )

    # endregion

    # region Fields method
    @api.depends('partner_id', 'partner_move_id')
    def _compute_active_move_equipment_ids(self):
        self.active_move_equipment_ids = self.partner_id.active_equipment_allocations_ids.mapped('equipment_id')
    # endregion

    # region Constrains and Onchange
    @api.onchange('partner_id')
    def _onchange_partner_equipment_ids(self):
        self.partner_equipment_ids = self.env['maintenance.equipment'].search([
            ('owner_partner_id', '=', self.partner_id.id),
        ])

    @api.onchange('equipment_id')
    def _on_change_partner_equipment_ids(self):
        if self.equipment_id:
            self.chip_number = self.equipment_id.chip_number
            self.tub_number = self.equipment_id.tub_number
            self.equipment_category_id = self.equipment_id.category_id
        else:
            self.chip_number = False
            self.tub_number = False
            self.equipment_category_id = False

    @api.depends('new_production_point_id')
    def _compute_equipment_stay_in_production_point(self):
        production_point = self.new_production_point_id
        allocations = self.env['partner.move.equipment.rel'].search([
            ('move_id.production_point_id', '=', production_point.id),
            ('category_id.equipment_follows_producer', '=', False),
            ('is_active', '=', True),
            ('end_date', '=', False),
            '|',
            ('move_id.is_active', '=', False),
            ('move_id.end_date', '<', self.env.context.get('default_new_situation_date')),
        ])

        self.equipment_stay_in_production_point = allocations
        self.has_active_stay_equipment = True if allocations else False

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_move_old_production_point_equipment(self, refresh=True, old_allocations=False, partner_move_id=False):
        self.ensure_one()

        old_allocations = old_allocations or self.old_partner_move_id.allocation_ids.filtered('is_active')

        #  Pour chaque dotation de l'ancien emménagement
        for old_allocation in old_allocations:
            if old_allocation.category_id.equipment_follows_producer is True:
                # On met fin aux dotations de l'ancien emménagement
                old_allocation.write({
                    'end_date': fields.Datetime.from_string(self.new_situation_date)
                })

                # On créée une nouvelle dotation sur le nouvel emménagement
                self.env['partner.move.equipment.rel'].create({
                    'equipment_id': old_allocation.equipment_id.id,
                    'move_id': partner_move_id.id if partner_move_id else self.partner_move_id.id,
                    'start_date': self.new_situation_date,
                })

        if refresh:
            return self._self_refresh_wizard()

    def action_change_old_residence_type(self):
        u"""Surcharge pour récupérer les bacs de l'ancien emmménagement."""
        old_allocations = self.old_partner_move_id.allocation_ids.filtered('is_active')

        result = super(EquipmentSetUpPartner, self).action_change_old_residence_type()

        self.action_move_old_production_point_equipment(
            False, old_allocations, partner_move_id=self.old_partner_move_id)

        return result

    def action_create_or_move_equipment(self):
        self.ensure_one()

        if not self.equipment_category_id and not self.chip_number and not self.tub_number and not self.equipment_id:
            raise ValidationError(_("You may enter some data"))

        # Partie bacs
        if self.env.context.get('create_equipment') and self.equipment_category_id \
                and (self.chip_number or self.tub_number):
            equipment_id = self.env['maintenance.equipment'].create({
                'category_id': self.equipment_category_id.id,
                'owner_partner_id': self.partner_id.id,
                'use_product': self.equipment_category_id.use_product,
                'product_id':
                    self.equipment_category_id.product_id
                    and self.equipment_category_id.product_id.id,
                'chip_number': self.chip_number,
                'tub_number': self.tub_number,
                'capacity': self.equipment_category_id.capacity,
                'capacity_unit_id':
                    self.equipment_category_id.capacity_unit_id
                    and self.equipment_category_id.capacity_unit_id.id,
            })

            self.env['partner.move.equipment.rel'].create({
                'equipment_id': equipment_id.id,
                'move_id': self.partner_move_id.id,
                'start_date': self.new_situation_date,
            })

        if self.env.context.get('move_equipment') and self.equipment_id:
            # On met fin à la dotation active du bac
            self.equipment_id.allocation_ids.filtered('is_active').write({
                'end_date': fields.Datetime.from_string(self.new_situation_date)
            })

            # On crée une nouvelle dotation
            self.env['partner.move.equipment.rel'].create({
                'start_date': fields.Datetime.from_string(self.new_situation_date),
                'move_id': self.partner_move_id.id,
                'equipment_id': self.equipment_id.id,
            })

        self.equipment_category_id = False
        self.equipment_id = False
        self.chip_number = False
        self.tub_number = False

        return self._self_refresh_wizard()

    def action_attribute_selected_equipment(self):

        old_allocations = self.attribution_stay_equipment

        #  Pour chaque dotation de l'ancien production point choisie
        for old_allocation in old_allocations:
            if old_allocation.category_id.equipment_follows_producer is False:
                # On met fin aux dotations de l'ancien production point choisie
                old_allocation.write({
                    'end_date': fields.Datetime.from_string(self.new_situation_date)
                })

                # On créée une nouvelle dotation sur le production point
                self.env['partner.move.equipment.rel'].create({
                    'equipment_id': old_allocation.equipment_id.id,
                    'move_id': self.partner_move_id.id,
                    'start_date': self.new_situation_date,
                })

        return self._self_refresh_wizard()

    # endregion

    # region Model methods

    def action_next_stage(self):
        self.ensure_one()

        self.equipment_category_id = False
        self.equipment_id = False
        self.chip_number = False
        self.tub_number = False

        return super(EquipmentSetUpPartner, self).action_next_stage()

    def end_old_partner_move(self):
        """Overwrite to move equipments if set so."""
        super(EquipmentSetUpPartner, self).end_old_partner_move()
        self.action_move_old_production_point_equipment(refresh=False)

    # endregion

    pass
