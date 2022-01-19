import logging
from datetime import datetime, date
from itertools import groupby

from odoo import models, fields, api, _, exceptions
from odoo.osv import expression
from ..tools import date_utils

_logger = logging.getLogger(__name__)


class HoranetPackage(models.Model):
    # region Private attributes
    _name = 'horanet.package'
    _inherit = ['horanet.subscription.shared', 'mail.thread']
    _sql_constraints = [('unicity_on_code', 'UNIQUE(code)', _("The code must be unique"))]
    _description = "package"

    # endregion

    # region Default methods
    def _default_code(self):
        return self.env['ir.sequence'].next_by_code('contract.code')

    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", compute='_compute_name', readonly=False, store=True,
                       track_visibility='always')
    code = fields.Char(string="Code", default=_default_code, copy=False, required=True)

    recipient_id = fields.Many2one(
        string="Recipient",
        comodel_name='res.partner',
        index=True,
    )
    subscription_id = fields.Many2one(
        string="Contract",
        comodel_name='horanet.subscription',
        domain="[('client_id', '=?', recipient_id)]",
        index=True,
        ondelete='cascade')

    line_ids = fields.One2many(string="Periods", comodel_name='horanet.package.line',
                               inverse_name='package_id')
    active_line_id = fields.Many2one(string="Active period", compute='_compute_active_line_id',
                                     comodel_name='horanet.package.line', store=False)

    prestation_id = fields.Many2one(string="Prestation", comodel_name='horanet.prestation')
    service_id = fields.Many2one(
        string="Service",
        comodel_name='horanet.service',
        required=False
    )
    activity_ids = fields.Many2many(
        string="Activities",
        comodel_name='horanet.activity',
        readonly=True,
        related='service_id.activity_ids',
        store=False,
    )
    is_blocked = fields.Boolean(string="Is blocked", default=True,
                                track_visibility='onchange')
    is_salable = fields.Boolean(string="Is salable")
    cycle_id = fields.Many2one(
        string="Cycle",
        comodel_name='horanet.subscription.cycle',
        readonly=True,
        required=True)
    cycle_id_period_type = fields.Selection(
        string="Cycle period",
        related='cycle_id.period_type',
        store=False)
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
    opening_date = fields.Datetime(
        string="Opening date",
        help="Date at which the package is active",
        required=False)
    closing_date = fields.Datetime(
        string="Closing date",
        help="Date at which the subscription is inactive")

    # Defined in horanet.subscription.date
    display_opening_date = fields.Char(help="Date at which the package is active")
    display_closing_date = fields.Char(help="Date at which the package is inactive")
    state = fields.Selection(help="Package state")
    # endregion

    balance = fields.Integer(string="Balance")

    use_product = fields.Boolean(string="Set a price")
    product_id = fields.Many2one(string="Product", comodel_name='product.template')
    invoice_type = fields.Selection(
        string="Invoice type",
        selection=[('beginning', "Beginning"),
                   ('ending', "Ending")])
    cycle_id_period_type = fields.Selection(
        string="Cycle period",
        related='prestation_id.cycle_id.period_type',
        store=False)
    is_renewable = fields.Boolean(
        string="Renewable",
        default=False)

    # region on_create
    on_create = fields.Boolean(string="Expert creation", default=True, store=False)
    on_create_prestation_id = fields.Many2one(
        string="Prestation",
        comodel_name='horanet.prestation',
        store=False)
    on_create_start_date = fields.Date(string="Start date", default=fields.Date.context_today, store=False)
    on_create_end_date = fields.Date(string="End date", store=False)
    on_create_prorata_temporis = fields.Boolean(string="Apply prorata", default=True, store=False)
    on_create_immediate_opening = fields.Boolean(string="Immediate opening", default=False, store=False)
    on_create_recipient_id = fields.Many2one(
        string="Recipient",
        comodel_name='res.partner',
        default=False,
        store=False)
    on_create_subscription_id = fields.Many2one(
        string="Contract",
        comodel_name='horanet.subscription',
        domain="[('client_id', '=?', on_create_recipient_id)]",
        default=False,
        store=False)

    is_derogation = fields.Boolean(
        string="Is derogation",
        compute='_compute_package_is_derogation',
        search='_search_package_is_derogation',
        store=False,
        help="The property derogation is inherent to the free packages without balance control and no cycle"
    )

    # endregion

    # endregion

    # region Fields method
    @api.depends('is_salable', 'is_blocked', 'cycle_id')
    def _compute_package_is_derogation(self):
        for rec in self:
            is_derogation = False
            if not rec.is_salable and not rec.is_blocked and rec.cycle_id.period_type == 'unlimited':
                is_derogation = True
            rec.is_derogation = is_derogation

        return

    @api.model
    def _search_package_is_derogation(self, operator, value):
        if operator not in ['=', '!=']:
            raise NotImplementedError("Got operator '%s' (expected '=' or '!=')" % operator)

        domain = ['&', '&',  # Il est critique de normaliser le domain en explicitant les opérateurs
                  ('is_salable', '=', False),
                  ('is_blocked', '=', False),
                  ('cycle_id.period_type', '=', 'unlimited')]

        # Négation du domaine en cas de recherche négative
        if bool(operator not in expression.NEGATIVE_TERM_OPERATORS) != bool(value):
            domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(domain)

    @api.depends()
    def _compute_active_line_id(self):
        """Compute the active line of the package at the current date.

        Set active_line_id to False if there is no active package lines.
        """
        search_date = fields.Datetime.now()

        for package in self:
            package.active_line_id = package.get_active_line(search_date)

    @api.depends('prestation_id', 'recipient_id')
    def _compute_name(self):
        """Compute the name of the package."""
        for rec in self:
            names = []
            if rec.prestation_id:
                names.append(rec.prestation_id.name)
            if rec.recipient_id:
                names.append(rec.recipient_id.name)
            if not names:
                names.append(rec.code)
            rec.name = ' '.join(names)

    # endregion

    # region Constrains and Onchange
    @api.onchange('prestation_id')
    def _onchange_package_prestation_id(self):
        self.ensure_one()
        if self.prestation_id:
            self.env.context = self.with_context(skip_onchange_prestation=True).env.context
            self.use_product = self.prestation_id.use_product
            self.product_id = self.prestation_id.product_id and self.prestation_id.product_id.id
            self.cycle_id = self.prestation_id.cycle_id.id
            self.service_id = self.prestation_id.service_id and self.prestation_id.service_id.id
            self.is_blocked = self.prestation_id.is_blocked
            self.invoice_type = self.prestation_id.invoice_type
            self.is_salable = self.prestation_id.is_salable
            self.balance = self.prestation_id.balance

    @api.onchange('use_product', 'product_id', 'cycle_id', 'service_id', 'is_blocked', 'is_salable',
                  'balance', 'invoice_type')
    def _onchange_prestation_inherited_settings(self):
        self.ensure_one()
        if self.env.context.get('skip_onchange_prestation'):
            return
        elif self.prestation_id:
            self.prestation_id = None

    @api.onchange('on_create_recipient_id')
    def _onchange_on_create_recipient_id(self):
        """Generate a domain used to filter subscription templates designed for the selected partner (if any)."""
        domain = []
        if self.on_create_recipient_id:
            allowed_prestations = self.on_create_prestation_id.search(
                [('required_category_domain', 'in', self.on_create_recipient_id)])
            domain.append(('id', 'in', allowed_prestations.ids))
        if self.env.context.get('package_filter_only_derogation', False):
            domain.append(('is_derogation', '=', True))

        return {'domain': {'on_create_prestation_id': domain}}

    @api.onchange('recipient_id')
    def _onchange_package_recipient_id(self):
        """Generate a domain used to filter subscription templates designed for the selected partner (if any)."""
        domain = {'prestation_id': []}
        if self.on_create_recipient_id:
            allowed_prestations = self.prestation_id.search(
                [('required_category_domain', 'in', self.prestation_id)])
            domain.update({'prestation_id': [('id', 'in', allowed_prestations.ids)]})

        return {'domain': domain}

    @api.onchange('on_create_subscription_id')
    def _onchange_on_create_subscription_id(self):
        """Generate a domain used to filter package recipient based on the subscription."""
        domain = {'on_create_recipient_id': []}
        if self.on_create_subscription_id:
            subscription_partners = self.env['res.partner']
            subscription_partners += self.on_create_subscription_id.client_id
            subscription_partners += self.on_create_subscription_id.package_ids.mapped('recipient_id')
            # Remove duplicates
            subscription_partners = subscription_partners & subscription_partners

            domain.update({'recipient_id': [('id', 'in', subscription_partners.ids)]})

            if len(subscription_partners) == 1:
                self.on_create_recipient_id = subscription_partners

        return {'domain': domain}

    @api.onchange('subscription_id')
    def _onchange_package_subscription_id(self):
        """Generate a domain used to filter package recipient based on the subscription."""
        domain = {'recipient_id': []}
        if self.subscription_id:
            subscription_partners = self.env['res.partner']
            subscription_partners += self.subscription_id.client_id
            subscription_partners += self.subscription_id.package_ids.mapped('recipient_id')
            # Remove duplicates
            subscription_partners = subscription_partners & subscription_partners

            domain.update({'on_create_recipient_id': [('id', 'in', subscription_partners.ids)]})

            if len(subscription_partners) == 1:
                self.recipient_id = subscription_partners

        return {'domain': domain}

    @api.constrains('is_renewable')
    def _check_protected_fields(self):
        for rec in self:
            if rec.state == 'done':
                raise exceptions.ValidationError(_("Can't change the renewable option of a 'done' package"))

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """Override to create the package with pseudo wizard embeded in view form."""
        if vals.get('on_create', False):
            # En mode pseudo wizard de création, c'est la méthode on_create qui rappellea le create
            result = self._on_create_package(vals)
        else:
            result = super(HoranetPackage, self).create(vals)

        return result

    @api.model  # noqa 901
    def create_package(self, prestation, subscription, opening_date=None, prorata_temporis=False,
                       recipient_id=None, closing_date=None):
        """Constructeur de package a partir d'une prestation pour un contrat (prestation).

        :param prestation: record of the horanet.prestation used to initialize the package
        :param subscription: Subscription which the package should be linked
        :param opening_date: date UTC (not datetime) on which the subscription became active,
        If False, the package will start immediately (datetime UTC)
        :param closing_date: optional, the date a which the package is not active
        :param prorata_temporis: boolean to tell if we should split balance and quantity on package lines
        :param recipient_id: optional a res.partner, if none the subscription.client_id will be used
        """
        opening_date = opening_date or fields.Datetime.now()
        if isinstance(opening_date, (date, datetime)):
            opening_date = fields.Datetime.to_string(opening_date)

        if closing_date:
            if isinstance(closing_date, str):
                closing_date = closing_date
            elif isinstance(closing_date, (date, datetime)):
                closing_date = fields.Datetime.to_string(opening_date)
            else:
                raise ValueError("Closing date must be a datetime" % str(recipient_id))

        if closing_date and opening_date and closing_date <= opening_date:
            raise UserWarning(_("The closing_date must be superior to the opening date"))

        if recipient_id and isinstance(recipient_id, int):
            recipient_id = self.env['res.partner'].browse(recipient_id)
            if not recipient_id:
                raise ValueError("Recipient id %s not found" % str(recipient_id))
        if recipient_id and not isinstance(recipient_id, models.Model):
            raise TypeError("The argument 'recipient_id' must be a recordset not a {bad_type}".format(
                bad_type=str(type(recipient_id))))
        if recipient_id and isinstance(recipient_id, models.Model) and recipient_id._name != 'res.partner':
            raise TypeError("The argument 'recipient_id' should be a recordset of "
                            "'res.partner' not {bad_type}".format(bad_type=str(type(recipient_id._name))))
        if recipient_id:
            recipient_id.ensure_one()

        if subscription and isinstance(subscription, int):
            subscription = self.env['horanet.subscription'].browse(subscription)
            if not subscription:
                raise ValueError("Susbscription id %s not found" % str(subscription))

        if prestation and isinstance(prestation, int):
            prestation = self.env['horanet.prestation'].browse(prestation)
            if not prestation:
                raise ValueError("Prestation id %s not found" % str(prestation))

        if subscription.opening_date > opening_date:
            # Dans le cas peu commun ou l'on décide de créer un package commençant avant son contrat,
            # il faut modifier la date de début du contrat
            subscription.update_active_period(opening_date=opening_date)

        new_package = self.create({
            'cycle_id': prestation.cycle_id.id,
            'invoice_type': prestation.invoice_type,
            'is_blocked': prestation.is_blocked,
            'is_salable': prestation.is_salable,
            'balance': prestation.balance,
            'service_id': prestation.service_id.id,
            'prestation_id': prestation.id,
            'subscription_id': subscription.id,
            'recipient_id': (recipient_id or subscription.client_id).id,
            'use_product': prestation.use_product,
            'product_id': prestation.product_id.id,
            'start_date': prestation.cycle_id.get_start_date_of_cycle(opening_date),
            'opening_date': opening_date,
            'closing_date': closing_date,
            'is_renewable': subscription.is_renewable
        })

        new_package._compute_package_line()
        if prorata_temporis:
            new_package._compute_prorata_temporis()

        return new_package

    @api.model
    def _create_packages_from_template(self, subscription_ids, prorata_temporis=False):
        u"""Create packages according to subscription template if there are none.

        Cette méthode est utilisée dans les données de démonstration, car elle permet de créer un
        abonnement 'manuellement', puis grace à cette méthode créer les forfaits de l'abonnement.
        Ainsi, l'abonnement possède un xml_id (puisque créée manuellement) qui peut être utilisé
        pour d'autres données de démo.

        :param subscription_ids: list<integer> horanet.subscription ids
        :param prorata_temporis: boolean to tell if we should split balance and quantity on package lines
        """
        subscriptions = self.env['horanet.subscription'].browse(subscription_ids)
        for rec in subscriptions.filtered('subscription_template_id'):
            if rec.subscription_template_id.prestation_ids and not rec.package_ids:
                for prestation in rec.subscription_template_id.prestation_ids:
                    self.create_package(prestation, rec, rec.opening_date, prorata_temporis)

    @api.model
    def _on_create_package(self, vals):
        """Pseudo creation wizard, used to create a subscription without using a custom TransientModel."""
        if 'on_create' in vals:
            del vals['on_create']
        if not vals.get('on_create_prestation_id', False):
            raise exceptions.UserError("Missing prestation")
        if not vals.get('on_create_recipient_id', False):
            raise exceptions.UserError("Missing package recipient")
        if not vals.get('on_create_immediate_opening', False) and not vals.get('on_create_start_date', False):
            raise exceptions.UserError("Missing start date if not immediate opening")

        opening_date = None
        if not vals.get('on_create_immediate_opening', False):
            opening_date = vals.get('on_create_start_date', fields.Date.today())

        closing_date = vals.get('on_create_end_date', False)

        # Appel du constructeur custom de subscription
        result = self.create_package(
            vals['on_create_prestation_id'],
            vals['on_create_subscription_id'],
            opening_date,
            vals.get('on_create_prorata_temporis', False),
            vals.get('on_create_recipient_id', False),
            closing_date,
        )

        return result

    @api.multi
    def write(self, vals):
        """Override to ensure that some values can't be modified."""
        if vals.get('cycle_id', False) and self.ids:
            raise exceptions.ValidationError(_("Can't change the cycle of an existing package"))
        else:
            result = super(HoranetPackage, self).write(vals)

        return result

    # endregion

    # region Actions
    @api.multi
    def compute_package(self, compute_date=None):
        """Création et mise à jour des lignes, à une éventuelle datetime.

        Basé sur les information du cycle du modèle et ses dates d'ouverture/clôture, cette méthode
        créé les lignes ou les mets à jour.

        Elle ne met pas à jours les packages.

        :param compute_date:
        :return: Nothing
        """
        compute_date = compute_date or fields.Datetime.to_string(datetime.utcnow().date())
        self._compute_package_line(compute_date)

    @api.multi
    def _compute_package_line(self, compute_date=None):
        self._compute_object_line(compute_date)

    @api.multi
    def end_package(self, end_date, prorata_temporis):
        """End given packages with given date.

        :param end_date: date given by the ORM
        """
        current_date = fields.Date.context_today(self)

        for rec in self:
            cycle_end_date = rec.cycle_id.get_end_date_of_cycle(current_date)
            rec.write({
                'closing_date': end_date,
                'end_date': cycle_end_date
            })
        self.mapped('active_line_id').end_package_line(end_date, prorata_temporis)

    @api.multi
    def action_compute_package(self):
        if self.filtered(lambda p: not p.opening_date):
            raise exceptions.Warning("An opening date is necessary in order to compute the package")
        self.compute_package()

    # endregion

    # region Model methods
    @api.multi
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
            no_start_date_package = self.filtered(lambda p: not p.start_date)
            if no_start_date_package:
                package_by_cycle = [(cycle, [pack for pack in group])
                                    for cycle, group in groupby(no_start_date_package, lambda p: p.cycle_id)]
                for cycle, liste_package in package_by_cycle:
                    no_start_date_package.filtered(lambda p: p in liste_package).write({
                        'start_date': cycle.get_start_date_of_cycle(opening_date)
                    })

        if closing_date:
            closing_date = date_utils.convert_date_to_closing_datetime(closing_date)
        date_values.update({'closing_date': closing_date})
        if remove_closing_date:
            date_values.update({'closing_date': False})
        if date_values:
            self.write(date_values)
        self._compute_package_line()
        if prorata:
            self._compute_prorata_temporis()

    @api.multi
    def prepare_sale_order_lines_qty_delivered(self, date_start='1900-01-01', date_end=False):
        """
        Call the method to update the quantity delivered on sale order lines.

        :param date_start: date start
        :param date_end: date end
        :return: list of updated sale order lines
        """
        sol_ids = self.env['sale.order.line']

        # On met la date de fin à aujourd'hui (à moins d'être Marty MC fly) si il n'y en a pas
        if not date_end:
            date_end = fields.Date.today()

        date_end = fields.Datetime.to_string(date_utils.convert_date_to_closing_datetime(date_end))

        # Pour les packages en pre facturation
        pre_packages = self.search([('id', 'in', self.ids),
                                    '|', ('invoice_type', '=', 'beginning'), ('invoice_type', '=', False)])
        # On prend les lignes qui ont une période en commun
        pre_package_lines = self.env['horanet.package.line'].search([('package_id', 'in', pre_packages.ids),
                                                                     ('end_date', '>', date_start),
                                                                     ('start_date', '<', date_end)])
        # Pour les packages en post facturation
        post_packages = self.search([('invoice_type', '=', 'ending'), ('id', 'in', self.ids)])
        post_package_lines = self.env['horanet.package.line'] \
            .search(['&', ('package_id', 'in', post_packages.ids),
                     '|', ('state', '=', 'closed'), ('state', '=', 'done')]
                    ).filtered(lambda r:
                               date_end >= r.closing_date >= date_start + " 00:00:00"
                               or date_end >= r.opening_date >= date_start + " 00:00:00")

        if pre_package_lines:
            sol_ids += pre_package_lines.update_sale_order_lines_qty_delivered(date_start, date_end)

        if post_package_lines:
            sol_ids += post_package_lines.update_sale_order_lines_qty_delivered(date_start, date_end)

        return sol_ids

    @api.multi
    def get_balance(self, activities=None, date_time=None):
        """Retourne la somme des soldes des lignes active de package (non bloqué).

        :param activities: Optionnel, un ou plusieurs record 'horanet.activity', utilisé pour filtrer les forfaits
        :param date_time: la date à laquelle le solde doit être calculé
        :return int: Le solde cumulé restant
        """
        if activities and not isinstance(activities, models.Model):
            raise ValueError("Bad Argument 'activities' should be a recordset")
        if activities:
            affected_package = self.filtered(lambda p: activities <= p.activity_ids)
        else:
            affected_package = self

        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        search_date_time = date_time or self.env.context.get('force_time', datetime.now())

        active_lines = affected_package.get_active_line(search_date_utc=search_date_time)
        return sum([rec.balance_remaining for rec in active_lines if rec.balance_remaining > 0])

    @api.multi
    def can_use(self, quantity, activities=None, date_time=None):
        """Détermine si le la quantité demandé est inférieur ou égale au solde restant.

        Cette méthode ne tiens compte que des lignes actives

        :param activities: Optionnel, un ou plusieurs record 'horanet.activity', utilisé pour filtrer les forfaits
        :param quantity: La quantité à décompter du solde
        :return boolean: True si le solde est suffisant, False sinon
        """
        if activities and not isinstance(activities, models.Model):
            raise ValueError("Bad Argument 'activities' should be a recordset")
        # Si aucun forfait n'existe, retourner False car il n'existe pas de droits
        if len(self) == 0:
            return False
        if activities:
            affected_package = self.filtered(lambda p: activities <= p.activity_ids)
        else:
            affected_package = self

        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        date_time = date_time or self.env.context.get('force_time', datetime.now())

        active_lines = affected_package.get_active_line(search_date_utc=date_time)

        if not active_lines:
            return False

        # Si il exist un forfait illimité, le solde est "infini"
        if active_lines.filtered(lambda r: not r.is_blocked):
            result = True
        else:
            result = (active_lines.get_balance() >= quantity)
        return result

    @api.multi
    def get_active_line(self, search_date_utc=None):
        """Return if it exists, the active lines at the specified date.

        :param search_date_utc: the date used to search the package.line (in UTC)
        :return: None or a package.line recordset
        """
        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        search_date_time = search_date_utc or self.env.context.get('force_time', datetime.now())

        if isinstance(search_date_time, (datetime, date)):
            search_date_time = fields.Datetime.to_string(search_date_time)
        elif isinstance(search_date_time, str):
            search_date_time = fields.Datetime.to_string(fields.Datetime.from_string(search_date_time))
        else:
            raise ValueError('search_date_utc must be an Odoo date (str) or date object')

        search_active_domain = self._search_state('=', 'active', search_date_utc=search_date_time)
        package_lines = self.env['horanet.package.line']

        active_packages_ids = self.search(
            [('id', 'in', self.ids)] + search_active_domain).with_context(prefetch_fields=False).ids

        if active_packages_ids:
            package_lines = self.env['horanet.package.line'].search(
                [('package_id', 'in', active_packages_ids)] + search_active_domain)

        return package_lines or None

    @api.multi
    def _compute_prorata_temporis(self, prestation=None):
        """Recompute the prorata of each line.

        after compute line

        :return:
        """
        for package in self:
            prestation = prestation or package.prestation_id
            # On ne peut calculer le prorata que si le package possède une prestation (pour le moment)
            if not prestation:
                continue
            for package_line in package.line_ids:
                if not package_line.end_date or not package_line.closing_date:
                    continue
                ratio = prestation.get_prorata_fraction(
                    package_line,
                    package_line.start_date, package_line.end_date,
                    package_line.opening_date, package_line.closing_date
                )
                balance = round((ratio or 1) * package_line.package_id.balance)
                package_line.write({
                    'package_price_prorata': ratio,
                    'balance_initial': balance})

    # endregion

    pass
