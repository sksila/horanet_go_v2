# coding: utf-8

from odoo import fields, models, _, tools, api
import json

STATES = [('not_processed', 'Not processed'), ('error', 'Error'), ('processed', 'Processed')]


class PickupImports(models.Model):
    # region Private attributes
    _name = 'equipment.pickup.import'
    _inherit = ['mail.thread']
    _rec_name = 'code'
    _sql_constraints = [('unicity_code', 'UNIQUE(code)', _('The import code value must be unique'))]
    _order = 'import_date desc'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    code = fields.Char(string="Code")
    data = fields.Text(string="Data", required=True)
    errors = fields.Text(string="Errors")
    comment = fields.Text(string="Comment", track_visibility='onchange')
    import_date = fields.Datetime(string="Import date", default=fields.Datetime.now, track_visibility='onchange')
    created_operations_count = fields.Integer(string="Created operations", default=0, readonly=True)
    data_count = fields.Integer(string="Data count", default=0, readonly=True)
    display_count = fields.Char(string="Processed data", compute="_compute_display_count", readonly=True)
    first_pickup_date = fields.Datetime(string="First pickup", readonly=True)
    last_pickup_date = fields.Datetime(string="Last pickup", readonly=True)
    state = fields.Selection(string='State', selection=STATES, default='not_processed', copy=False,
                             track_visibility='onchange')

    # endregion

    # region Fields method
    @api.multi
    @api.depends('created_operations_count', 'data_count')
    def _compute_display_count(self):
        """
        Compute display count.

        Get the ratio between created operations and total data received.
        """
        for rec in self:
            rec.display_count = str(rec.created_operations_count) + " / " + str(rec.data_count)

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """Set the code of the import with a sequence if not provided."""
        if not vals.get('code', False):
            sequence = self.env.ref('environment_equipment.seq_equipment_pickup_import')
            vals['code'] = sequence.sudo().next_by_id()
        return super(PickupImports, self).create(vals)
    # endregion

    # region Actions
    def action_process_data(self):
        """Create all the operations."""
        for rec in self:
            try:
                data = json.loads(rec.data)
            except Exception as e:
                rec.errors = tools.ustr(e)
                continue

            nb_operations_created, errors = rec.create_operation(data)

            if errors:
                errors.append(_("{} operations created").format(str(nb_operations_created)))
                rec.errors = '<br/>'.join(errors)
                rec.state = 'error'
            else:
                rec.errors = ""
                rec.state = 'processed'

            rec.created_operations_count = nb_operations_created
            rec.data_count = len(data)
    # endregion

    # region Model methods
    def get_pickup_date(self, pickup, errors):
        """
        Return the pickup date form a pickup.

        :param pickup: the pickup with its data
        :param errors: errors
        :return: the pickup date
        """
        pickup_date = pickup.get('pickup_date', False)
        if not pickup_date:
            errors.append(_('Pickup date not provided in line: ') + str(pickup.values()))
            return False

        try:
            fields.Datetime.from_string(pickup_date)
        except Exception:
            errors.append(_("Wrong pickup date format in line: {}. Provide date in format: Y-m-d H:M:S").format(
                str(pickup.values())))
            return False

        return pickup_date

    def get_chip_number(self, pickup, errors):
        """
        Return the chip number of a pickup.

        :param pickup: the pickup with its data
        :param errors: errors
        :return: chip_number (str)
        """
        chip_number = pickup.get('chip_number')

        if not chip_number:
            errors.append(_('Chip number not provided in line: ') + str(pickup.values()))
            return False

        return chip_number

    @api.multi
    def create_operation(self, data):
        self.ensure_one()

        operation_model = self.env['horanet.operation']
        errors = []
        nb_operations_created = 0

        for pickup in data:
            # Get data
            pickup_date = self.get_pickup_date(pickup, errors)
            chip_number = self.get_chip_number(pickup, errors)

            # 2 Check data parts (and go to next data if wrong)
            if not pickup_date or not chip_number:
                continue

            # Set first and last pickup date
            if not self.first_pickup_date or pickup_date < self.first_pickup_date:
                self.first_pickup_date = pickup_date

            if not self.last_pickup_date or pickup_date > self.last_pickup_date:
                self.last_pickup_date = pickup_date

            equipments = self.env['maintenance.equipment'].search([('chip_number', '=', chip_number)])

            equipment = equipments

            # As equipments are not unique per chip number we need to retrieve
            # the container and loop over its allocations to find the one that was
            # active when the pickup was done
            for allocation in equipments.mapped('allocation_ids'):
                if allocation.start_date < pickup_date and \
                   (not allocation.end_date or allocation.end_date > pickup_date):
                    equipment = allocation.equipment_id
                    break

            if len(equipment) > 1:
                errors.append(
                    'No active allocation for equipment with chip number : %s '
                    'for date %s' % (chip_number, pickup_date))
                continue

            # We check if there is an equipment
            if equipment:
                # Check if the operation has not been created yet
                operation = operation_model.search([('maintenance_equipment_id', '=', equipment.id),
                                                    ('time', '=', pickup_date)])
                # get the move to get the partner
                equipment_move = equipment.get_equipment_move(search_date_utc=pickup_date)

                nb_operations_created += 1
                if not operation:
                    try:
                        new_operation = operation_model.create({
                            'quantity': 1,
                            'action_id': self.env.ref('environment_equipment.horanet_action_container_pickup').id,
                            'activity_id': equipment.category_id.activity_id.id,
                            'time': pickup_date,
                            'maintenance_equipment_id': equipment.id,
                            'partner_id': equipment_move and equipment_move.partner_id and equipment_move.partner_id.id,
                            'activity_sector_id': self.env.ref(
                                'environment_equipment.horanet_activity_sector_pickup').id,
                            'chip_read': pickup.get('chip_read'),
                            'equipment_allowed': pickup.get('equipment_allowed'),
                            'equipment_emptied': pickup.get('equipment_emptied'),
                            'equipment_broken': pickup.get('equipment_broken'),
                            'sorting_problem': pickup.get('sorting_problem'),
                            'size_exceeding': pickup.get('size_exceeding')
                        })
                        new_operation.write({'partner_id': equipment.owner_partner_id.id})
                    except Exception as e:
                        errors.append(_("Operation not created for line: {}. Error : {}")
                                      .format(str(pickup.values()), tools.ustr(e)))
            # Or warning
            else:
                errors.append(_("Equipment with chip {} not found").format(str(pickup.get('chip_number'))))

        return nb_operations_created, errors

    def pickup_import_pav_data_create(self, code=None, data=None):
        """Create pickup import.

        Call by the route /environment/container/data/create/ and sulo import
        """
        errors = []
        # 1 - Check data
        if not code:
            errors.append(_("Code not provided"))

        if not data:
            errors.append(_("Data not provided"))

        if not errors:
            # 2 - Save data
            pickup_import_model = self.env['equipment.pickup.import']

            pickup_import_data = pickup_import_model.search([('code', '=', code)])
            if pickup_import_data:
                # Mise à jour
                pickup_import_data.write({
                    'data': json.dumps(data),
                    'import_date': fields.Datetime.now(),
                    'state': 'not_processed',
                })
            else:
                # Création
                pickup_import_data = pickup_import_model.create({
                    'code': code,
                    'data': json.dumps(data),
                })

            # 3 - Process data
            pickup_import_data.action_process_data()
        else:
            pickup_import_data = False

        return errors, pickup_import_data
    # endregion

    pass
