# 1 : imports of python lib
import json
import logging

from odoo import models, api, fields, exceptions
from ..config import config

_logger = logging.getLogger(__name__)


class WizardActivityRuleSandbox(models.TransientModel):
    # region Private attributes
    _name = 'activity.rule.wizard.sandbox'
    _description = "go figure"
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    activity_rule_id = fields.Many2one(string="Rule to test", comodel_name='activity.rule',
                                       domain=[('state', 'in', ['active', 'inactive'])],
                                       help="go figure")

    # edit_rule_code = fields.Selection(string="Edit rule code", [('edit','Edit'),('')])

    # activity_rule_code = fields.Text(string="Rule code (edit)", related='activity_rule_id.rule_code')
    custom_rule_code = fields.Text(string="Rule code")
    execute_custom_rule_code = fields.Selection(string="Execute custom code",
                                                selection=[('yes', 'Yes'), ('no', 'No')],
                                                default='no')

    input_mode = fields.Selection(string="Mode", selection=config.ACTION_MODE, default='query')

    action_id = fields.Many2one(string="Action", comodel_name='horanet.action')
    device_id = fields.Many2one(string="Device", comodel_name='horanet.device')
    tag_id = fields.Many2one(string="Tag", comodel_name='partner.contact.identification.tag')
    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner')
    check_point_id = fields.Many2one(string="Check point", comodel_name='device.check.point')

    operation_is_offline = fields.Boolean(string="Is offline", default=False)
    operation_quantity = fields.Float(string="Quantity", default=1.0)
    operation_activity_id = fields.Many2one(string="Activity", comodel_name='horanet.activity')
    operation_query_id = fields.Many2one(string="Query", comodel_name='device.query')
    operation_sector_id = fields.Many2one(string="Sector", comodel_name='activity.sector')

    custom_action_code = fields.Char(string="Action code")
    custom_device_id = fields.Char(string="Device id")
    custom_check_point = fields.Char(string="Check point code")
    custom_activity_id = fields.Char(string="Activity code")
    custom_sector_code = fields.Char(string="Sector Code")
    query_time = fields.Datetime(string="Time context", default=fields.Datetime.now)

    sandbox_query_json = fields.Text(string="Sandbox query", readonly=True, compute='compute_sandbox_query_json')
    sandbox_operation_json = fields.Text(string="Sandbox operation", readonly=True)

    result_response_json = fields.Text(string="Result response")
    result_operation_json = fields.Text(string="Result operation")
    result_usage_json = fields.Text(string="Result usage")

    result_message = fields.Text(string="Execution message", readonly=True)

    raise_exception = fields.Boolean(string="Raise exception", default=False)

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    @api.constrains('tag_id', 'partner_id')
    def constraint_identification(self):
        """Verify the data."""
        self.ensure_one()
        if self.tag_id and self.partner_id:
            raise exceptions.ValidationError("Only one of the field Partner and Tag should be set")

    @api.onchange('activity_rule_id')
    def onchange_activity_rule_id(self):
        self.ensure_one()
        if self.activity_rule_id:
            self.custom_rule_code = self.activity_rule_id.rule_code
            self.execute_custom_rule_code = 'yes'
        else:
            self.execute_custom_rule_code = 'no'

    @api.onchange('action_id')
    def onchange_action_id(self):
        self.ensure_one()
        if self.action_id:
            self.custom_action_code = self.action_id.code

    @api.onchange('operation_sector_id')
    def onchange_operation_sector_id(self):
        self.ensure_one()
        self.custom_sector_code = self.operation_sector_id and self.operation_sector_id.code or False

    @api.onchange('custom_action_code')
    def onchange_custom_action_code(self):
        self.ensure_one()
        self.action_id = self.action_id.search([('code', '=like', self.custom_action_code)])

    @api.onchange('device_id')
    def onchange_device_id(self):
        self.ensure_one()
        if self.device_id:
            self.custom_device_id = self.device_id and self.device_id.unique_id

    @api.onchange('custom_device_id')
    def onchange_custom_device_id(self):
        self.ensure_one()
        self.device_id = self.device_id.search([('unique_id', '=like', self.custom_device_id)])

    @api.onchange('check_point_id')
    def onchange_check_point_id(self):
        self.ensure_one()
        if self.check_point_id:
            self.custom_check_point = self.check_point_id.code

    @api.onchange('custom_check_point')
    def onchange_custom_check_point(self):
        self.ensure_one()
        self.check_point_id = self.check_point_id.search([('code', '=like', self.custom_check_point)])

    @api.depends('custom_check_point', 'custom_device_id', 'custom_action_code')
    def compute_sandbox_query_json(self):
        self.sandbox_query_json = self._get_custom_query_json()

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_simulate_execution(self):
        trigger = False
        if self.input_mode == 'query':
            trigger = self.create_dummy_query(self.action_id,
                                              self.device_id,
                                              self.tag_id,
                                              self.partner_id,
                                              self.check_point_id,
                                              self.query_time)
        elif self.input_mode == 'operation':
            trigger = self.create_dummy_operation(self.action_id,
                                                  self.device_id,
                                                  self.tag_id,
                                                  self.partner_id,
                                                  self.operation_quantity,
                                                  self.check_point_id,
                                                  self.operation_activity_id,
                                                  self.operation_query_id,
                                                  self.operation_is_offline,
                                                  self.operation_sector_id,
                                                  self.query_time)

        custom_rule = False
        if self.execute_custom_rule_code == 'yes' and self.activity_rule_id:
            custom_rule = self.activity_rule_id.rule_dummy(self.custom_rule_code)

        exploitation_engine = self.env['exploitation.engine'].sudo().new({'trigger': trigger})
        engine_result = exploitation_engine.compute(simulation=True,
                                                    custom_rule=custom_rule,
                                                    force_time=self.query_time,
                                                    raise_exception=self.raise_exception)

        self.result_operation_json = json.dumps(
            [{'quantity': operation.quantity,
              'activity_id': operation.activity_id.read(['name']),
              } for operation in engine_result.operation_ids],
            indent=2, sort_keys=True, ensure_ascii=False)
        self.result_response_json = json.dumps(
            [{'message': response.message,
              'response': response.response,
              } for response in engine_result.response_id],
            indent=2, sort_keys=True, ensure_ascii=False)
        self.result_usage_json = json.dumps(
            [{'package_line_id': usage.package_line_id.read(['name']),
              'quantity': usage.quantity,
              'activity_id': usage.activity_id.read(['name']),
              } for usage in engine_result.usage_ids],
            indent=2, sort_keys=True, ensure_ascii=False)

        self.result_message = engine_result.execution_log

        return self._self_refresh_wizard()

    @api.multi
    def action_save_code(self):
        if self.activity_rule_id and self.custom_rule_code:
            self.activity_rule_id.rule_code = self.custom_rule_code
            new_rule = self.activity_rule_id.search([('code', '=', self.activity_rule_id.code)])
            self.activity_rule_id = new_rule

            return self._self_refresh_wizard()
        else:
            raise exceptions.ValidationError("Error when saving custom rule code")
        pass

    @api.multi
    def action_clear_execution(self):
        self.result_response_json = False
        self.result_operation_json = False
        self.result_usage_json = False
        self.result_message = False

    # endregion

    # region Model methods
    def create_dummy_query(self, action_rec, device_rec, tag_rec=None, partner_rec=None, checkpoint_rec=None,
                           force_time=None):
        dummy_query = self.env['device.query'].new({
            'action_id': action_rec,
            'tag_id': tag_rec,
            'partner_id': partner_rec,
            'device_id': device_rec,
            'check_point_id': checkpoint_rec,
            'time': force_time,
        })
        return dummy_query

    def create_dummy_operation(self, action_rec, device_rec, tag_rec, partner_rec=None, quantity=1, checkpoint_rec=None,
                               activity_rec=None, query_rec=None, is_offline=False, activity_sector_id=None,
                               force_time=None):
        dummy_query = self.env['horanet.operation'].new({
            'device_id': device_rec,
            'action_id': action_rec,
            'tag_id': tag_rec,
            'partner_id': partner_rec,
            'check_point_id': checkpoint_rec,
            'activity_id': activity_rec,
            'query_id': query_rec,
            'quantity': quantity,
            'is_offline': is_offline,
            'activity_sector_id': activity_sector_id,
            'time': force_time,
        })
        return dummy_query

    @api.multi
    def _get_custom_query_json(self):
        self.ensure_one()
        action = None
        tag = None
        device = None
        check_point = None
        if self.action_id:
            action = self.action_id.read(fields=['code', 'id', 'name', 'type'])[0]
        if self.tag_id:
            tag = self.tag_id.read(fields=['active', 'create_date', 'medium_id',
                                           'number', 'display_name', 'mapping_id'])[0]

        if self.device_id:
            device = self.device_id.read(fields=['check_point_ids', 'name', 'unique_id'])[0]
        if self.check_point_id:
            check_point = self.check_point_id.read(fields=['code', 'device_id', 'name'])[0]
        elif self.custom_check_point:
            check_point = {'code': self.custom_check_point}
        query = {
            'action': action,
            'tag': tag or None,
            'device': device,
            'check_point': check_point,
            'create_date': self.query_time or fields.datetime.now()
        }
        return json.dumps(query, indent=2, sort_keys=True)

    @api.multi
    def _self_refresh_wizard(self):
        return {
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

        # return {
        #     # TODO : une action vide pourrait être créée (action_manager.js) appelée ir.action.do_noting
        #     "type": "set_scrollTop",
        # }

    # endregion
    pass
