# coding: utf-8

from odoo import api, fields, models, _, exceptions


class DepositPoint(models.Model):
    # region Private attributes
    _name = 'environment.deposit.point'
    _inherit = 'maintenance.equipment'
    _sql_constraints = [('unicity_reference', 'UNIQUE(reference)', _('The reference value must be unique'))]
    # endregion

    # region Default methods
    def _default_reference(self):
        return self.env['ir.sequence'].next_by_code('deposit.point.reference')

    def _default_activity_ids(self):
        return self.env.ref('environment_deposit_point.horanet_activity_sector_pav').activity_ids
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name",
                       compute="compute_name",
                       readonly=True)

    deposit_area_id = fields.Many2one(
        string="Deposit area",
        required=True,
        comodel_name='environment.deposit.area'
    )

    activity_id = fields.Many2one(
        string="Waste",
        comodel_name='horanet.activity',
        domain="[('default_action_id.code', '=', 'DEPOT_PAV')]",
        required=True
    )

    reference = fields.Char(string="Reference",
                            required=True,
                            copy=False,
                            default=_default_reference)

    serial_no = fields.Char('Serial Number', required=True)

    filling_level = fields.Integer(string="Filling level")

    commissioning_date = fields.Date(string="Date of commissioning",
                                     default=fields.Date.context_today)

    volume = fields.Integer(string="Volume (litres)")

    last_import_date = fields.Date(string="Last import date")

    deposit_check_point_id = fields.Many2one(
        string="Deposit check point",
        comodel_name='device.check.point',
        help="Created automatically, not intended to display",
        readonly=True
    )

    operation_ids = fields.One2many(string="Deposits",
                                    comodel_name='horanet.operation',
                                    compute="_compute_operation_ids")

    pickup_ids = fields.One2many(string="Pickups",
                                 comodel_name='horanet.operation',
                                 compute="_compute_pickup_ids")

    city_id = fields.Many2one(
        string="City",
        comodel_name='res.city',
        compute='_compute_city_id',
        readonly=True,
        store=True
    )

    equipment_rel_ids = fields.One2many(string="Containers",
                                        comodel_name='deposit.point.equipment.rel',
                                        inverse_name='deposit_point_id')
    # endregion

    # region Fields method
    @api.multi
    @api.depends('deposit_check_point_id')
    def _compute_operation_ids(self):
        """
        Compute operations.

        Get the deposit operations made on that deposit point thanks to check point.
        """
        for rec in self:
            rec.operation_ids = self.env['horanet.operation'].sudo().search([
                ('activity_id.application_type', '=', 'environment'),
                ('action_id', '=', self.env.ref('environment_deposit_point.horanet_action_depot_pav').id),
                ('check_point_id', '=', rec.deposit_check_point_id.id),
            ], limit=20)

    @api.multi
    @api.depends('equipment_rel_ids')
    def _compute_pickup_ids(self):
        """
        Compute pickups operations.

        Get the pickup operations made on the containers of that deposit point.
        """
        for rec in self:
            pickup_ids = self.env['horanet.operation']
            for equipment_rel in rec.equipment_rel_ids:
                domain = [
                    ('activity_id.application_type', '=', 'environment'),
                    ('action_id', '=', self.env.ref('environment_equipment.horanet_action_container_pickup').id),
                    ('maintenance_equipment_id', '=', equipment_rel.maintenance_equipment_id.id),
                    ('time', '>=', equipment_rel.beginning_date),
                ]
                if equipment_rel.ending_date:
                    domain.append(('time', '<', equipment_rel.ending_date))

                pickup_ids += self.env['horanet.operation'].sudo().search(domain, limit=20)

            rec.pickup_ids = pickup_ids

    @api.depends('deposit_area_id', 'deposit_area_id.city_id')
    def _compute_city_id(self):
        for rec in self:
            rec.city_id = rec.deposit_area_id.city_id
    # endregion

    # region Constrains and Onchange
    @api.onchange('reference', 'deposit_area_id', 'activity_id')
    def compute_name(self):
        """Display name of the record."""
        for rec in self:
            name_parts = []
            if rec.reference:
                name_parts.append(rec.reference)
            if rec.deposit_area_id:
                name_parts.append(rec.deposit_area_id.name)
            if rec.activity_id:
                name_parts.append(rec.activity_id.name)
            rec.name = ' - '.join(name_parts)

    @api.constrains('deposit_area_id', 'activity_id')
    def _check_consistancy(self):
        """Deposit point's activity must be in deposit area's activity sector."""
        for rec in self:
            if rec.activity_id:
                if rec.activity_id not in \
                        self.env.ref('environment_deposit_point.horanet_activity_sector_pav').activity_ids:
                    raise exceptions.ValidationError(
                        _("The selected waste must be present in the deposit area's activity sector."))

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """
        Override to create a 'deposit' check-point if necessary.

        A checkpoint is created to associate the deposit point with the default activity sector of deposit areas
        (ref('environment_deposit_point.horanet_activity_sector_pav').
        this will be a check-point without device.
        """
        new_deposit_point = super(DepositPoint, self).create(vals)

        if vals.get('deposit_area_id', False):
            deposit_check_point_id = self.env['device.check.point'].sudo().create({
                'name': _("Auto generated for {reference} / {sector_name}").format(
                    reference=new_deposit_point.reference,
                    sector_name=self.env.ref('environment_deposit_point.horanet_activity_sector_pav').name),
                'input_activity_sector_id': self.env.ref('environment_deposit_point.horanet_activity_sector_pav').id,
                'infrastructure_id': new_deposit_point.deposit_area_id.infrastructure_id.id,
            })

            new_deposit_point.deposit_check_point_id = deposit_check_point_id

        return new_deposit_point

    @api.multi
    def write(self, vals):
        """
        Override to update a 'deposit' check-point if necessary.

        If there is no checkpoint associating the deposit point with the default activity sector of deposit areas
        (ref('environment_deposit_point.horanet_activity_sector_pav'), a check point is created and previous
        checkpoint is deleted.
        """
        if 'deposit_area_id' in vals or 'reference' in vals:
            for deposit_point in self:
                deposit_area = vals.get('deposit_area_id', False) \
                                and self.env['environment.deposit.area'].sudo().browse(vals['deposit_area_id']) \
                                or deposit_point.deposit_area_id

                # Créer ou mettre à jour le checkpoint de dépôt (automatiquement défini)
                cp_vals = {
                    'name': _("Auto generated for {reference} / {sector_name}").format(
                        reference=vals.get('reference', False) or deposit_point.reference,
                        sector_name=self.env.ref('environment_deposit_point.horanet_activity_sector_pav').name),
                    'input_activity_sector_id':
                        self.env.ref('environment_deposit_point.horanet_activity_sector_pav').id,
                    'infrastructure_id': deposit_area.infrastructure_id.id,
                }
                if deposit_point.deposit_check_point_id:
                    deposit_point.deposit_check_point_id.write(cp_vals)
                else:
                    deposit_point.deposit_check_point_id = self.env['device.check.point'].sudo().create(cp_vals)

        return super(DepositPoint, self).write(vals)

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})

        serial_no = self.serial_no.split("(")[0]
        copied_count = self.search_count(
            [('serial_no', '=like', u"{}%".format(serial_no))])

        default['serial_no'] = u"{}({})".format(serial_no, copied_count)

        return super(DepositPoint, self).copy(default)
        # endregion
