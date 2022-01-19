from ast import literal_eval
from datetime import datetime, timedelta

from odoo import api, models, fields
from odoo.osv import expression


class AddSubscriptionOnPartner(models.Model):
    """Add 'subscription' on partners."""

    # region Private attributes
    _name = 'res.partner'
    _inherit = ['res.partner']
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    available_subscription_template_ids = fields.Many2many(
        string="Available contract templates",
        comodel_name='horanet.subscription.template',
        compute='_compute_available_subscription_template_ids',
        store=False)

    subscription_ids = fields.One2many(
        string="Subscriptions",
        comodel_name='horanet.subscription',
        inverse_name='client_id')

    subscription_count = fields.Integer(
        string="Subscription count",
        compute='_compute_subscription_count',
        store=False)

    # endregion

    # region Fields method
    @api.depends('subscription_category_ids')
    def _compute_available_subscription_template_ids(self):
        """List of all contract template available for the partner."""
        for partner in self:
            partner.available_subscription_template_ids = self.env['horanet.subscription.template'].search(
                [('required_category_domain', 'in', partner)])

    @api.depends('subscription_ids')
    def _compute_subscription_count(self):
        """List of all contract template available for the partner."""
        for partner in self:
            partner.subscription_count = len(partner.subscription_ids)

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def open_partner_subscription(self):
        """Return an action that display subscriptions for the given partners."""
        action = self.env.ref('horanet_subscription.action_partner_subscription_tree').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('client_id', 'child_of', self.ids))
        if len(self) == 1:
            action['context'] = literal_eval(action['context'])
            action['context'].update({'default_on_create_client_id': self.id})

        return action

    # endregion

    # region Model methods

    @api.multi
    def get_operations(self, activities, time_delta):
        """Find the partner previous operations.

        :param activities: Use to filter operation by activities
        :param time_delta: Time the search in the past
        :return: A recordset of 'horanet.operation'
        """
        self.ensure_one()
        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        contextual_time = self.env.context.get('force_time', datetime.now())

        start_time = contextual_time

        if not time_delta:
            raise ValueError("The argument 'time_delta' is mandatory")
        if isinstance(time_delta, timedelta):
            start_time = start_time - time_delta

        # if time_delta not in ['hour', 'day', 'week', 'month', 'year']:
        #     timedelta(days=6)
        #     time_limit = datetime(year=today.year, month=today.month, day=today.day,)start_time.date() 'year'
        if activities and not isinstance(activities, models.Model):
            raise TypeError("The argument 'activities' must be a recordset not a {bad_type}".format(
                bad_type=str(type(activities))))
        if activities and isinstance(activities, models.Model) and activities._name != 'horanet.activity':
            raise TypeError("The argument 'activities' should be a recordset of "
                            "'horanet.activity' not {bad_type}".format(bad_type=str(type(activities._name))))

        result = self.env['horanet.operation'].search(
            expression.normalize_domain([('operation_partner_id', '=', self.id),
                                         ('time', '>=', fields.Datetime.to_string(start_time)),
                                         ('time', '<=', fields.Datetime.to_string(contextual_time)),
                                         ('activity_id', 'in', activities.ids)]))
        return result

    # endregion

    pass
