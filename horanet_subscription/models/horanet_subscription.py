import logging
import time
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, exceptions, _
from ..tools import date_utils

_logger = logging.getLogger(__name__)


class HoranetSubscription(models.Model):
    # region Private attributes
    _name = 'horanet.subscription'
    _inherit = ['application.type', 'horanet.subscription.shared', 'mail.thread']
    _order = "opening_date desc"

    # endregion

    # region Default methods
    def _default_code(self):
        return self.env['ir.sequence'].next_by_code('subscription.code')

    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", compute='_compute_name', readonly=False, store=True)
    code = fields.Char(string="Code", default=_default_code, copy=False, required=True, track_visibility='always')
    # region dates
    start_date = fields.Date(
        string="Technical start date",
        oldname='starting_date',
        readonly=True,
        required=False)
    end_date = fields.Date(
        string="Technical end date",
        oldname='ending_date',
        readonly=True)
    confirmation_date = fields.Datetime(
        string="Confirmation Date",
        readonly=True)
    opening_date = fields.Datetime(
        string="Opening date",
        help="Date at which the subscription is active",
        required=False)
    closing_date = fields.Datetime(
        string="Closing date",
        help="Date at which the subscription is inactive")

    # Defined in horanet.subscription.date
    display_opening_date = fields.Char(help="Date at which the subscription is active")
    display_closing_date = fields.Char(help="Date at which the subscription is inactive")
    state = fields.Selection(help="Subscription state")
    # endregion

    line_ids = fields.One2many(
        string="Periods",
        comodel_name='horanet.subscription.line',
        inverse_name='subscription_id',
        readonly=True)
    active_line_id = fields.Many2one(
        string="Active period",
        compute='_compute_active_line_id',
        comodel_name='horanet.subscription.line',
        store=False)

    package_ids = fields.One2many(
        string="Contract Lines",
        comodel_name='horanet.package',
        inverse_name='subscription_id')
    is_renewable = fields.Boolean(
        string="Renewable",
        default=False)
    client_id = fields.Many2one(
        string="Customer",
        comodel_name='res.partner',
        domain="[('customer', '=', True)]",
        index=True,
        track_visibility='onchange')
    subscription_template_id = fields.Many2one(
        string="Contract template",
        comodel_name='horanet.subscription.template',
        required=False)
    cycle_id = fields.Many2one(
        string="Cycle",
        comodel_name='horanet.subscription.cycle',
        readonly=False,
        required=True,
        track_visibility='onchange')
    cycle_id_period_type = fields.Selection(
        string="Cycle period",
        related='cycle_id.period_type',
        store=False)
    payment_type = fields.Selection(
        string="Payment type",
        selection=[('before', "Before"),
                   ('before_and_after', "Before and after"),
                   ('after', "After")],
        default='before',
        readonly=False,
        track_visibility='onchange')
    payment_term_id = fields.Many2one(
        string="Payment Terms",
        comodel_name='account.payment.term',
        track_visibility='onchange')

    # region on_create
    on_create = fields.Boolean(string="Expert creation", default=True, store=False)
    on_create_template_id = fields.Many2one(
        string="Contract template",
        comodel_name='horanet.subscription.template',
        store=False)
    on_create_start_date = fields.Date(string="Start date", default=fields.Date.context_today, store=False)
    on_create_prorata_temporis = fields.Boolean(string="Apply prorata", default=True, store=False)
    on_create_immediate_opening = fields.Boolean(string="Immediate opening", default=False, store=False)
    on_create_client_id = fields.Many2one(
        string="Customer",
        comodel_name='res.partner',
        default=False,
        domain="[('customer', '=', True)]", store=False)

    # endregion

    # endregion

    # region Fields method
    @api.depends()
    def _compute_active_line_id(self):
        """Compute the active line of the subscription of current date.

        Set active_line_id to False if the subscription is not active.
        """
        search_date = fields.Datetime.now()

        for subscription in self:
            subscription.active_line_id = subscription.get_active_line(search_date)

    @api.depends('subscription_template_id', 'client_id')
    def _compute_name(self):
        """Compute the name of the subscription."""
        for rec in self:
            names = []
            if rec.subscription_template_id:
                names.append(rec.subscription_template_id.name)
            if rec.client_id:
                names.append(rec.client_id.name)

            rec.name = ' '.join(names)

    # endregion

    # region Constrains and Onchange
    @api.onchange('on_create_client_id')
    def _onchange_on_create_client_id(self):
        """Generate a domain used to filter subscription templates designed for the selected partner (if any)."""
        domain = {'on_create_template_id': []}
        if self.on_create_client_id:
            allowed_templates = self.on_create_template_id.search(
                [('required_category_domain', 'in', self.on_create_client_id)])
            domain.update({'on_create_template_id': [('id', 'in', allowed_templates.ids)]})

        return {'domain': domain}

    @api.onchange('is_renewable')
    def _onchange_is_renewable(self):
        self.ensure_one()
        if self.cycle_id and self.cycle_id.period_type == 'unlimited':
            raise UserWarning(_("Can't change the renewable option of a subscription with an unlimited cycle"))
        if self.is_renewable:
            self.closing_date = False
        elif self.cycle_id:  # dans le cas de la création, le cycle n'existe pas encore
            self.closing_date = date_utils.convert_date_to_closing_datetime(
                self.cycle_id.get_end_date_of_cycle(
                    fields.Datetime.now()))

    @api.constrains('is_renewable')
    def _check_protected_fields(self):
        for sub in self:
            if sub.state == 'done':
                raise exceptions.ValidationError(_("Can't change the renewable option of a 'done' subscription"))

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """Override to create the subscription lines if the subscription is confirmed."""
        if vals.get('on_create', False):
            # En mode pseudo wizard de création, c'est la méthode on_create qui rappellea le create
            result = self._on_create_subscription(vals)
        else:
            result = super(HoranetSubscription, self).create(vals)

        return result

    @api.model
    def _on_create_subscription(self, vals):
        """Pseudo creation wizard, used to create a subscription without using a custom TransientModel."""
        if 'on_create' in vals:
            del vals['on_create']
        if not vals.get('on_create_template_id', False):
            raise exceptions.UserError("Missing subscription template")
        if not vals.get('on_create_client_id', False):
            raise exceptions.UserError("Missing subscription client")
        if not vals.get('on_create_immediate_opening', False) and not vals.get('on_create_start_date', False):
            raise exceptions.UserError("Missing start date if not immediate opening")

        opening_date = None
        if not vals.get('on_create_immediate_opening', False):
            opening_date = vals.get('on_create_start_date', fields.Date.today())

        # Appel du constructeur custom de subscription
        result = self.create_subscription(
            [vals['on_create_client_id']],
            vals['on_create_template_id'],
            opening_date,
            vals.get('on_create_prorata_temporis', False),
            True)
        return result

    @api.model
    def create_subscription(self, partner_ids, template_id,
                            opening_date=False, prorata_temporis=False, confirmation=False):
        """Create multiple subscriptions.

        :param partner_ids: list of partners ids
        :param template_id: id of the subscription_template
        :param opening_date: date UTC (not datetime) on which the subscription became active,
        If False, the subscription will start immediately (datetime UTC)
        :param prorata_temporis: boolean to tell if we should split balance and quantity on package lines
        """
        template_rec = None
        if template_id:
            if not isinstance(template_id, int):
                raise exceptions.UserError(_("template_id: expected int type, got %s") % type(template_id))
            else:
                template_rec = self.env['horanet.subscription.template'].browse(template_id)
                if not template_rec:
                    raise ValueError("Template id %s not found" % str(template_id))

        if not isinstance(partner_ids, (list, tuple)):
            raise exceptions.UserError(_("partner_ids: expected list or tuple type, got %s") % type(partner_ids))

        opening_date = opening_date or fields.Datetime.now()

        new_subscriptions = self.env['horanet.subscription']

        subscriptions = self.env['horanet.subscription']
        for partner_id in partner_ids:
            create_vals = {
                'subscription_template_id': template_rec.id,
                'client_id': partner_id,
                'cycle_id': template_rec.cycle_id.id,
                'confirmation_date': confirmation and fields.Datetime.now() or None,
                'opening_date': opening_date,
                'application_type': template_rec.application_type,
                'payment_type': template_rec.payment_type,
                'is_renewable': template_rec.is_renewable,
                'start_date': template_rec.cycle_id.get_start_date_of_cycle(opening_date)
            }
            # Dans le cas d'un abonnement non renouvelable et si le cycle n'est pas illimité,
            # positionner la date de clôture à la date de fin du cycle
            if not template_rec.is_renewable and template_rec.cycle_id.period_type != 'unlimited':
                create_vals.update({
                    'closing_date': date_utils.convert_date_to_closing_datetime(
                        template_rec.cycle_id.get_end_date_of_cycle(opening_date))})
            new_subscriptions += self.create(create_vals)

        # Création des lignes des nouveaux abonnements, normalement inutile car effectué par le create
        new_subscriptions._compute_subscription_line()

        # Ajout des packages si le template en défini
        if template_rec.prestation_ids:
            package_model = self.env['horanet.package']
            for subscription in new_subscriptions:
                for prestation in template_rec.prestation_ids:
                    package_model.create_package(
                        prestation, subscription, opening_date, prorata_temporis)
            subscriptions += subscription

        return subscriptions

    # endregion

    # region Actions

    @api.multi  # noqa: C901
    def update_active_period(self, opening_date=None, closing_date=None, prorata=False, remove_closing_date=False):
        """Entry point to change the opening and closing date of subscriptions.

        This methode will cascade the change to the related packages.

        :param opening_date: Optional, a datetime (UTC) of the opening date
        :param closing_date: Optional, a datatime (UTC) representing the closing date
        :param prorata: If True, the eventual packages lines updated will update their prorata
        :param remove_closing_date: If True, the closing date will be set to None
        :return: Nothing
        """
        date_values = {}
        # TODO Test input values ...
        if closing_date and remove_closing_date:
            raise ValueError("Incoherence, can't remove closing date AND set closing date. Pick one")

        if opening_date:
            date_values.update({'opening_date': opening_date})
        if closing_date:
            closing_date = date_utils.convert_date_to_closing_datetime(closing_date)
            closing_date = fields.Datetime.to_string(closing_date)
            date_values.update({'closing_date': closing_date})
        if remove_closing_date:
            date_values.update({'closing_date': False})
        if date_values:
            self.write(date_values)
        self._compute_subscription_line()

        # Iteration sur les packages, pour modifier leurs dates si les nouvelles dates sont plus restrictives
        for subscription in self:
            for package in subscription.package_ids:
                new_opening_date = None
                # Vérifier à ne pas réduire la date d'ouverture
                if opening_date:
                    if not package.opening_date:
                        new_opening_date = opening_date
                    if package.opening_date and package.opening_date <= opening_date:
                        new_opening_date = opening_date

                new_closing_date = None
                # Vérifier à ne pas augmenter la date de fermeture (si déjà fermé)
                if closing_date:
                    if not package.closing_date:
                        new_closing_date = closing_date
                    if package.closing_date and package.closing_date >= closing_date:
                        new_closing_date = closing_date

                # En cas de fermeture avant ouverture et inversement :
                if package.opening_date and new_closing_date and package.opening_date > new_closing_date:
                    new_closing_date = package.opening_date
                if package.closing_date and new_opening_date and package.closing_date < new_opening_date:
                    new_opening_date = package.closing_date

                if new_opening_date or new_closing_date or prorata:
                    package.update_active_period(new_opening_date, new_closing_date, prorata)

    @api.multi
    def action_confirm_subscription(self):
        """Confirm the contract and set the confirmation date."""
        for rec in self:
            if not rec.opening_date:
                rec.opening_date = fields.Datetime.now()
            if not rec.start_date:
                rec.start_date = fields.Date.today()

        self.write({'confirmation_date': fields.Datetime.now()})

    @api.multi
    def action_compute_subscription(self):
        draft_contract = self.filtered(lambda s: s.state == 'draft')
        if draft_contract:
            raise UserWarning(_("Draft subscription should not be computed"))
        self.compute_subscription()

    # endregion

    # region Model methods
    @api.multi
    def compute_subscription(self, compute_date=None):
        """Création et mise à jour des lignes, à une éventuelle datetime.

        Basé sur les information du cycle du modèle et ses dates d'ouverture/clôture, cette méthode
        créé les lignes ou les mets à jour.

        Elle ne met pas à jours les packages.

        :param compute_date:
        :return: Nothing
        """
        compute_date = compute_date or fields.Datetime.to_string(datetime.utcnow().date())
        self._compute_subscription_line(compute_date)
        for subscription in self:
            subscription.package_ids.compute_package(compute_date)

    @api.multi
    def _compute_subscription_line(self, compute_date=None):
        self._compute_object_line(compute_date)

    @api.multi
    def get_active_line(self, search_date_utc=None):
        """Return if it exist the active line at the specified date.

        :param search_date_utc: the date used to search the subscription.line (in UTC)
        :return: None or an subscription.line record
        """
        self.ensure_one()
        search_date_time = search_date_utc or self.env.context.get('force_time', datetime.now())

        if isinstance(search_date_time, (datetime, date)):
            search_date_time = fields.Datetime.to_string(search_date_time)
        elif isinstance(search_date_time, str):
            search_date_time = fields.Datetime.to_string(fields.Datetime.from_string(search_date_time))
        else:
            raise ValueError('search_date_utc must be an Odoo date (str) or date object')

        search_active_domain = self._search_state('=', 'active', search_date_utc=search_date_time)
        result = self.env['horanet.package.line']

        active_subscriptions_ids = self.search(
            [('id', 'in', self.ids)] + search_active_domain).with_context(prefetch_fields=False).ids

        if active_subscriptions_ids:
            result = self.env['horanet.subscription.line'].search(
                [('subscription_id', 'in', active_subscriptions_ids)] + search_active_domain)

        return result or None

    # endregion

    # region external?
    @api.multi
    def prepare_sale_order_lines_qty_delivered(self, prestation_id=False, start_date="1900-01-01", end_date=False):
        """Add doc.

        :param prestation_id:
        :param start_date:
        :param end_date:
        :return:
        """
        domain = [('subscription_id', 'in', self.ids), ('state', '!=', 'draft')]
        if prestation_id:
            domain.append(('prestation_id', '=', prestation_id.id))
        packages = self.env['horanet.package'].search(domain)

        return packages and packages.prepare_sale_order_lines_qty_delivered(
            date_start=start_date, date_end=end_date) or self.env['sale.order.line']

    @api.model
    def _cron_compute_all_contracts_sale_orders(self, options=None):
        """Compute all the contracts to sale."""
        start_time = time.time()
        package_line_model = self.env['horanet.package.line']

        options = options or {}
        limit = options.get('limit', None)
        offset = options.get('offset', 0)

        cron = self.env.ref('horanet_subscription.mega_contracts_sale_order_scheduler')

        package_lines = package_line_model.search([], limit=limit, offset=offset)

        if package_lines:
            try:
                cron.active = False
                self.env.cr.commit()

                _logger.info('Cron: Starting computing contracts for sale')
                package_line_model.bill_package_lines(package_lines)
                _logger.info("Cron: end of computing in {exec_time}s"
                             .format(exec_time=round(time.time() - start_time, 3)))
            finally:
                cron.active = True
                cron.args = "({'offset':%i,'limit':%i},)" % (offset + limit, limit)

    @api.model
    def _cron_compute_subscription(self, options=None):
        """Search for active subscriptions and update them."""
        options = options or {}

        hours_offset = options.get('hours_offset', 1)
        limit = options.get('limit', 100)
        cron = self.env.ref('horanet_subscription.subscription_update_scheduler')
        try:
            cron.active = False
            self.env.cr.commit()

            compute_date = datetime.now() + relativedelta(hours=hours_offset)
            compute_date_orm = fields.Datetime.to_string(compute_date)

            _logger.info("Cron Job: Search for subscriptions to compute. (at :{time_search} UTC)".format(
                time_search=str(compute_date_orm)))

            domain_for_sub_to_compute = self._search_state('=', 'to_compute', search_date_utc=compute_date_orm)

            all_subscriptions_to_compute = self.search(domain_for_sub_to_compute).with_context({
                'tracking_disable': True})

            offset = 0
            number_to_update = len(all_subscriptions_to_compute)

            if number_to_update:
                _logger.info("Cron Job: {subscription_count} subscriptions found.".format(
                    subscription_count=str(number_to_update)))
            else:
                _logger.info("Cron Job: No subscription tu update, All subscription are up to date.")

            while all_subscriptions_to_compute[offset:(limit + offset)]:
                subscriptions = all_subscriptions_to_compute[offset:(limit + offset)]
                start_time = time.time()
                subscriptions.compute_subscription()
                _logger.info("Cron Job: Updated {number} subscriptions in {time_s} seconds ({current}/{total})."
                             " (first id {start_id} "
                             "last id {end_id})".format(start_id=str(subscriptions[0].id),
                                                        end_id=str(subscriptions[-1].id),
                                                        current=str(offset + limit),
                                                        total=str(number_to_update),
                                                        number=str(len(subscriptions)),
                                                        time_s=str(round(time.time() - start_time, 3))))
                self.env.cr.commit()

                offset = offset + limit

            _logger.info("Cron: End update ({number} subscriptions updated)".format(
                number=str(number_to_update)))
        finally:
            cron.active = True

    # endregion

    pass
