# coding: utf-8

from odoo import fields, models, _, tools, api
from odoo.tools import safe_eval
import json

STATES = [('not_processed', 'Not processed'), ('error', 'Error'), ('processed', 'Processed')]


class DepositArea(models.Model):
    # region Private attributes
    _name = 'deposit.import.data'
    _inherit = ['mail.thread']
    _rec_name = 'code'
    _sql_constraints = [('unicity_code', 'UNIQUE(code)', _('The import code value must be unique'))]
    _order = 'import_date desc'

    # endregion

    # region Default methods
    def _get_default_mapping_pav(self):
        return safe_eval(self.env['ir.config_parameter'].get_param(
            'partner_contact_identification.default_deposit_point_mapping_id', 'False'
        ))
    # endregion

    # region Fields declaration
    code = fields.Char(string="Code",
                       required=True)

    data = fields.Text(
        string="Data",
        required=True)

    errors = fields.Text(string="Errors")

    comment = fields.Text(string="Comment",
                          track_visibility='onchange')

    import_date = fields.Datetime(string="", default=fields.Datetime.now,
                                  track_visibility='onchange')

    created_operations_count = fields.Integer(string="Created operations", default=0, readonly=True)

    data_count = fields.Integer(string="Data count", default=0, readonly=True)

    display_count = fields.Char(string="Processed data", compute="_compute_display_count", readonly=True)

    first_deposit_date = fields.Datetime(string="First deposit", readonly=True)

    last_deposit_date = fields.Datetime(string="Last deposit", readonly=True)

    state = fields.Selection(string='State',
                             selection=STATES,
                             default='not_processed',
                             copy=False,
                             track_visibility='onchange')

    deposit_point_mapping_id = fields.Many2one(
        string="Mapping",
        comodel_name='partner.contact.identification.mapping',
        default=lambda self: self._get_default_mapping_pav(),
        domain="[('mapping', '=', 'csn')]",
    )
    # endregion

    # region Fields method
    # endregion

    #
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
    # endregion

    # region Actions
    @api.multi
    def action_process_data(self):

        operation_model = self.env['horanet.operation']

        for rec in self:
            if rec.state == 'processed':
                continue

            errors = []

            nb_operations_created = 0

            try:
                data = json.loads(rec.data)
            except Exception as e:
                errors.append(tools.ustr(e))
                data = []

            for deposit_data in data:

                # 1 Get data parts
                # 1.1 - Get tag
                tag = self.get_tag(deposit_data, errors)

                # 1.2 - Get deposit point
                deposit_point = self.get_deposit_point(deposit_data, errors)

                # 1.3 - Get deposit date
                deposit_date = self.get_deposit_date(deposit_data, errors)

                # 2 Check data parts (and go to next data if wrong)
                if not tag or not deposit_point or not deposit_date:
                    continue

                # 3 Update dates
                if not rec.first_deposit_date or deposit_date < rec.first_deposit_date:
                    rec.first_deposit_date = deposit_date

                if not rec.last_deposit_date or deposit_date > rec.last_deposit_date:
                    rec.last_deposit_date = deposit_date

                deposit_point.last_import_date = rec.import_date

                # 4 Create operation
                # 4.1 - Verify if the operation already exists (and do nothing if it exists)
                operation = operation_model.search([
                    ('time', '=', deposit_date),
                    ('tag_id', '=', tag.id),
                    ('deposit_point_id', '=', deposit_point.id),
                ])

                # 4.2 - Create the operation if it doesn't exists
                if not operation:
                    try:
                        operation_model.create({
                            'quantity': 1,
                            'action_id': deposit_point.activity_id.default_action_id.id,
                            'tag_id': tag.id,
                            'activity_id': deposit_point.activity_id.id,
                            'check_point_id': deposit_point.deposit_check_point_id.id,
                            'deposit_point_id': deposit_point.id,
                            'infrastructure_deposit_area_id': deposit_point.deposit_area_id.id,
                            'time': deposit_date,
                        })

                    except Exception as e:
                        errors.append(_("Operation not created for line: {}. Error : {}")
                                      .format(str(deposit_data.values()), tools.ustr(e)))

                nb_operations_created += 1

            if errors:
                errors.append(_("{} operations created").format(str(nb_operations_created)))
                rec.errors = '<br/>'.join(errors)
                rec.state = 'error'
            else:
                rec.errors = ""
                rec.state = 'processed'

            rec.created_operations_count = nb_operations_created
            rec.data_count = len(data)

            # return errors, nb_operations_created
    # endregion

    # region Model methods
    def get_tag(self, deposit_data, errors):
        tag_model = self.env['partner.contact.identification.tag']

        if not deposit_data.get('tag_number', False):
            errors.append(_('Tag number not provided in line: ') + str(deposit_data.values()))
            return False

        tag = tag_model.with_context(active_test=False).search([
            ('number', '=', deposit_data['tag_number']),
            ('mapping_id', '=', self._get_default_mapping_pav()),
        ])

        if not tag:
            errors.append(_('Tag not found for line: ') + str(deposit_data.values()))

        return tag

    def get_deposit_point(self, deposit_data, errors):
        deposit_point_model = self.env['environment.deposit.point']

        if not deposit_data.get('serial_number', False):
            errors.append(_('Serial number not provided in line: ') + str(deposit_data.values()))
            return False

        deposit_point = deposit_point_model.search([('serial_no', '=', deposit_data['serial_number'])])

        if not deposit_point:
            errors.append(_('Deposit point not found for line: ') + str(deposit_data.values()))

        return deposit_point

    def get_deposit_date(self, deposit_data, errors):
        deposit_date = deposit_data.get('deposit_date', False)
        if not deposit_date:
            errors.append(_('Deposit date not provided in line: ') + str(deposit_data.values()))
            return False

        try:
            fields.Datetime.from_string(deposit_date)
        except Exception:
            errors.append(_("Wrong deposit date format in line: {}. Provide date in format: Y-m-d H:M:S").format(
                str(deposit_data.values())))
            return False

        return deposit_date

    def deposit_import_pav_data_create(self, code=None, data=None, mapping_id=None):
        """Method for the deposit import data, we create deposit from file.

        Call by the route /environment/pav/data/create/
        """
        errors = []

        # 1 - Check data
        if not code:
            errors.append(_("Code not provided"))

        if not data:
            errors.append(_("Data not provided"))

        mapping_id = mapping_id or safe_eval(self.env['ir.config_parameter'].get_param(
            'partner_contact_identification.default_deposit_point_mapping_id', 'False'
        ))

        if not mapping_id:
            errors.append(_("Mapping not provided"))

        if not self.env['partner.contact.identification.mapping'].search([('id', '=', mapping_id)]):
            errors.append(_("Provided mapping does not exist"))

        if errors:
            return errors, False

        # 2 - Save data
        deposit_import_data_model = self.env['deposit.import.data']
        deposit_import_data = deposit_import_data_model.search([('code', '=', code)])
        if deposit_import_data:
            # Mise à jour
            deposit_import_data.write({
                'data': json.dumps(data),
                'deposit_point_mapping_id': mapping_id,
                'import_date': fields.Datetime.now(),
                'state': 'not_processed',
            })
        else:
            # Création
            deposit_import_data = deposit_import_data_model.create({
                'code': code,
                'deposit_point_mapping_id': mapping_id,
                'data': json.dumps(data),
            })

        # 3 - Process data
        deposit_import_data.action_process_data()

        return errors, deposit_import_data

    # endregion

    pass
