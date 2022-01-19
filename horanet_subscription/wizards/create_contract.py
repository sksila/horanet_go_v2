from odoo import fields, models, api, _

try:
    from odoo.addons.horanet_go.tools.utils import format_log

except ImportError:
    from horanet_go.tools.utils import format_log


class CreateContractWizard(models.TransientModel):
    _name = 'subscription.wizard.create.contract'

    subscription_template_id = fields.Many2one(
        string="Contract template",
        comodel_name='horanet.subscription.template',
        required=True
    )

    start_date = fields.Date(default=fields.Date.context_today)
    prorata_temporis = fields.Boolean()

    existing_subscription_ids = fields.Many2many(
        string="List of subscriptions that already exist",
        comodel_name='horanet.subscription',
        compute='_compute_existing_subscription_ids',
    )

    message_box = fields.Text(
        string="Display message",
        compute='_compute_message_box',
        store=False)

    @api.depends('subscription_template_id', 'start_date')
    def _compute_existing_subscription_ids(self):
        for rec in self:
            if rec.subscription_template_id:
                active_ids = self.env.context.get('active_ids')
                partners = self.env['res.partner'].browse(active_ids)
                active_subscription = self.wizard_contract_get_active_subscription(partners,
                                                                                   rec.subscription_template_id,
                                                                                   rec.start_date)

                if active_subscription:
                    rec.existing_subscription_ids = [(6, 0, active_subscription.ids)]

    @api.depends('subscription_template_id', 'start_date')
    def _compute_message_box(self):
        self.ensure_one()

        message = ''
        if self.subscription_template_id:
            active_ids = self.env.context.get('active_ids')
            partners_selected = self.env['res.partner'].browse(active_ids)
            active_subscription = self.wizard_contract_get_active_subscription(partners_selected,
                                                                               self.subscription_template_id,
                                                                               self.start_date)

            partner_active_subscription = active_subscription.mapped('client_id')

            partners_final = list(set(partners_selected.ids) - set(partner_active_subscription.ids))
            if partner_active_subscription and len(partners_final) > 0:

                message += "<b><warning>{title}</warning></b>:\n\t{text} {nb_partner} {message}\n".format(
                    title=_("Remark"),
                    text=_("Some"),
                    nb_partner=_(str(len(partner_active_subscription)) + "/" +
                                 str(len(partners_selected))),
                    message=_("partners already have an active, a pending or a new subscription "
                              "for this subscription template. If you don't want to attribute another "
                              "contract use the button 'Create contract for partner without contract'."))

            elif partner_active_subscription and len(partners_final) == 0:
                message += "<b><warning>{title}</warning></b>:\n\t{text} {nb_partner} {message}\n".format(
                    title=_("Remark"),
                    text=_("All"),
                    nb_partner=_(str(len(partner_active_subscription)) + "/" +
                                 str(len(partners_selected))),
                    message=_("partners already have an active, a pending or a new subscription "
                              "for this subscription template. If you don't want to attribute another "
                              "contract use the button 'Create contract for partner without contract'."))

        self.message_box = message and format_log(message) or False

    def create_contract(self, partners=False, subscription_template=False):
        """
        Create the contracts for partners for a specified template.

        :param partners: partners to create contracts
        :param subscription_template: the subscription template to use
        :return: None
        """
        # partners is the context if not passed to the call..
        # may be caused by not having @api.multi decorator
        if isinstance(partners, dict):
            partners = self.env['res.partner'].browse(partners.get('active_ids'))

        if not partners:
            return
        subscription_template_id = subscription_template or self.subscription_template_id

        self.env['horanet.subscription'].create_subscription(
            partners.ids,
            subscription_template_id.id,
            self.start_date,
            self.prorata_temporis)

    def create_contract_unique(self):
        """Create contracts for partner who hasn't a active contract for the subscrition templace selected."""
        if self.subscription_template_id:
            active_ids = self.env.context.get('active_ids')
            partners_selected = self.env['res.partner'].browse(active_ids)
            active_subscription = self.wizard_contract_get_active_subscription(partners_selected,
                                                                               self.subscription_template_id,
                                                                               self.start_date)
            partner_active_subscription = active_subscription.mapped('client_id')

            partners_final = list(set(partners_selected.ids) - set(partner_active_subscription.ids))
            # partners_to_create_contracts = self.env['res.partner'].search([('id', 'in', partners_final)])
            partners_to_create_contracts = self.env['res.partner'].browse(partners_final)

            self.create_contract(partners_to_create_contracts)

    def wizard_contract_get_active_subscription(self, partners, subscription_template, start_date):
        """Get actives, news or pending subscriptions for a subscription_template and a start date selected.

        :param partners: records of partners
        :param subscription_template: template of the subscription
        :param start_date: start date of the subscription
        :return: list of subscription
        """
        active_subscription = self.env['horanet.subscription'].search([
            '|',
            '|',
            ('state', '=', 'active'), ('state', '=', 'pending'),
            '|',
            ('state', '=', 'draft'), ('state', '=', 'to_compute'),
            ('client_id', 'in', partners.ids),
            ('subscription_template_id', '=', subscription_template.id),
            '|',
            ('closing_date', '=', False), ('closing_date', '>', start_date)

        ])
        return active_subscription
