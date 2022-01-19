
import ast
import logging
from odoo import api, models, fields, _
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    is_environment_service_provider = fields.Boolean(
        string='Is an environment service provider',
        compute='_compute_is_environment_service_provider',
        search='_search_is_environment_service_provider')

    environment_subscription_id = fields.Many2one(
        string="Environment contract",
        comodel_name='horanet.subscription',
        compute='_compute_environment_subscription_id',
        search='_search_environment_subscription_id'
    )
    environment_package_ids = fields.One2many(
        string="Contract lines",
        comodel_name='horanet.package',
        compute='_compute_environment_package_ids',
        search='_search_environment_package_ids'
    )
    has_active_environment_subscription = fields.Boolean(
        string="Has active environment contract",
        compute='_compute_has_active_environment_subscription',
        search='_search_has_active_environment_subscription'
    )

    is_environment_producer = fields.Boolean(
        string="Is environment producer",
        compute=lambda x: '',
        search='_search_is_environment_producer',
        readonly=True,
        store=False,
    )

    display_name2 = fields.Char(
        string="Second Names",
        compute='compute_display_name2',
        search='_search_display_name2',
        store=False,
    )
    derogation_count = fields.Integer(
        string=u"Dérogations",
        compute='_compute_derogation_count',
        store=False,
    )
    setup_and_close_wizards_enabled = fields.Boolean(
        string="Setup and close wizards enabled",
        compute='_compute_setup_and_close_wizards_enabled',
    )

    environment_pickup_contract_ids = fields.One2many(
        string="Pickup contracts",
        comodel_name='environment.pickup.contract',
        inverse_name='service_provider_id',
    )
    environment_pickup_contract_count = fields.Integer(
        string="Pickup contracts count",
        compute='_compute_partner_environment_pickup_contract_count',
        store=False
    )
    # endregion

    # region Fields method
    def _compute_company_type(self):
        u"""On surcharge la méthode de base pour mettre en pro si on est dans le menu pro.

        On ne créer un pro que si il n'y a pas de prénom,
        cela évite qu'un contact d'une company soit créé en pro.
        """
        super(ResPartner, self)._compute_company_type()
        for partner in self:
            context = self.env.context
            if context.get('create_partner_pro', False) and not partner.firstname:
                partner.company_type = 'company'

    def _compute_partner_environment_pickup_contract_count(self):
        for partner in self:
            partner.environment_pickup_contract_count = len(partner.environment_pickup_contract_ids)

    @api.depends()
    def _compute_environment_subscription_id(self):
        for rec in self:
            rec.environment_subscription_id = rec.subscription_ids.search([
                ('client_id', '=', rec.id),
                ('application_type', '=', 'environment'),
                ('state', '=', 'active')
            ], limit=1)

    def _search_environment_subscription_id(self, operator, value):
        subscription_model = self.env['horanet.subscription']
        partner_model = self.env['res.partner']
        partner_ids = partner_model

        # Si value = False
        if not value:
            subscriptions = subscription_model.search([('application_type', '=', 'environment')])
            # Pour gagner du temps si la recherche est du type ('environment_subscription_id', '!=', False)
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                partners = partner_model.search([('subscription_ids', 'in', subscriptions.ids)])
                return [('id', 'in', partners.ids)]
            # Sinon si c'est du type ('environment_subscription_id', '=', False)
            partners = partner_model.search([('subscription_ids', 'not in', subscriptions.ids)])
            return [('id', 'in', partners.ids)]

        elif isinstance(value, int) or isinstance(value, list):
            subscriptions = subscription_model.browse(value)
            partner_ids = subscriptions.mapped('client_id')

        domain = [('id', 'in', partner_ids.ids)]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain.insert(0, expression.NOT_OPERATOR)

        return domain

    @api.model
    def _search_subscription_category_ids_for_all_producer(self, operator, value):
        """Deprecated, use `defined OR` during catgories search instead."""
        u"""Recherche de partner ayant une ou plusieurs catégories (La recherche est une recherche en OU inclusif).

        Copie de la méthode de recherche de subscription_category_ids (horanet_go/inherited_partner.py)
        Mais on remplace le And par un OR inclusif pour regrouper les domains cad P in C1 C2 --> P in C1 + P in C2
        (on normalise le domain de recherche avant de faire le OR).
        Cette modification est nécessaire car on passe en argument une value qui est une list ou le domain de
        chaque catégorie de la list peut exclure les autres éléments
        (exemple: domain de value[0]=[is_company=True] et domain de value[1]=[is_company=True])

        :param operator: Un des opérateurs suivant : 'in', 'not in', '=', '!=', 'like', 'ilike'
        :param value: une catégorie (record), un id ou une liste d'id de catégorie, ou le code de la catégorie
        :return: Un domaine de recherche de res.partner
        """
        result = expression.FALSE_DOMAIN

        if isinstance(value, str):
            categories = self.subscription_category_ids.search([('code', operator, value)])
        elif operator in ['in', 'not in', '=', '!=']:
            categories = self.env['subscription.category.partner']
            if isinstance(value, models.Model) and value._name == 'subscription.category.partner':
                categories = value
            elif value and not isinstance(value, list) and isinstance(value, int):
                categories = categories.browse([value])
            elif value and isinstance(value, list):
                categories = categories.browse(value)

        domains = [expression.normalize_domain(ast.literal_eval(domain)) for domain in categories.mapped('domain')]
        if domains:
            result = expression.OR(domains)
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            result = [expression.NOT_OPERATOR] + result

        return expression.normalize_domain(result)

    def _search_is_environment_producer(self, operator, value):
        u"""Recherche des partenaire ayant une catégorie flaggé "producteur" et ayant un contrat d'environnement."""
        producer_categories = self.env['subscription.category.partner'].search([('is_environment_producer', '=', True)])

        # création du domaine positif
        domain = expression.normalize_domain(
            expression.AND([
                [('has_active_environment_subscription', '=', True)],
                expression.OR(
                    [[('subscription_category_ids', 'in', cate)] for cate in producer_categories]
                )
            ])
        )
        # Inversion en cas de recherche négative
        if bool(operator in expression.NEGATIVE_TERM_OPERATORS) == bool(value):
            domain = [expression.NOT_OPERATOR] + domain

        return domain

    @api.depends()
    def _compute_environment_package_ids(self):
        package_model = self.env['horanet.package']

        for rec in self:

            rec.environment_package_ids = package_model.search([
                ('recipient_id', '=', rec.id),
                ('prestation_id.activity_ids.application_type', '=', 'environment'),
                ('state', '=', 'active')
            ]).ids

    def _search_environment_package_ids(self, operator, value):
        package_model = self.env['horanet.package']
        packages = package_model.browse(value)

        domain = [('id', 'in', packages.mapped('recipient_id').ids)]

        # Si on n'a pas de valeur, typiquement ('environment_package_ids', '=', False)
        # Autrement dit on cherche tout les partners n'ayant pas de package
        # Alors on fait une comparaison entre tous les partners et ceux qui ont un package
        if not value:
            partners = self.env['res.partner'].search([])
            partner_with_packages = package_model.search([]).mapped('recipient_id')
            partner_with_no_packages = partners - partner_with_packages
            domain = [('id', 'in', partner_with_no_packages.ids)]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain.insert(0, expression.NOT_OPERATOR)

        return domain

    @api.depends('environment_subscription_id')
    def _compute_has_active_environment_subscription(self):
        for rec in self:
            rec.has_active_environment_subscription = bool(
                rec.environment_package_ids.search([
                    ('id', 'in', rec.environment_package_ids.ids),
                    ('state', '=', 'active'),
                ])
            ) or bool(
                rec.environment_subscription_id.search([
                    ('id', 'in', rec.environment_subscription_id.ids),
                    ('state', '=', 'active'),
                ])
            )

    def _search_has_active_environment_subscription(self, operator, value):
        subscription_model = self.env['horanet.subscription']
        active_environment_subscriptions_rec = subscription_model.search([
            ('application_type', 'in', ['environment']),
            ('state', '=', 'active'),
        ])

        domain = [('subscription_ids', 'in', active_environment_subscriptions_rec.ids)]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain.insert(0, expression.NOT_OPERATOR)

        return domain

    @api.depends('lastname2', 'firstname2')
    def compute_display_name2(self):
        """Compute the display name2."""
        for rec in self:
            rec.display_name2 = ' '.join([
                rec.lastname2 or (rec.firstname2 and rec.lastname) or '',
                rec.firstname2 or ''
            ]).strip() or False

    def _search_display_name2(self, operator, value):
        """Search the display name2."""
        if not isinstance(value, str):
            return []

        search_name = '%%%s%%' % value
        res_domain = []
        if ' ' not in value:
            res_domain = ['|',
                          ('firstname2', operator, search_name),
                          ('lastname2', operator, search_name),
                          ]
        else:
            cr = self.env.cr
            query = """SELECT p.id AS partner_id
                        FROM
                            (SELECT TRIM(regexp_replace(
                                COALESCE(lastname2, lastname, '')|| ' '||
                                COALESCE(firstname2, ''),
                                 '\s+', ' ', 'g'))
                                AS display_name1,
                                TRIM(regexp_replace(
                                COALESCE(firstname2, '')|| ' '||
                                COALESCE(lastname2, lastname, ''),
                                 '\s+', ' ', 'g'))
                                AS display_name2, id
                            FROM res_partner) AS p
                        WHERE p.display_name1 {operator1} {percent1}
                        OR p.display_name2 {operator2} {percent2}""".format(
                operator1=operator,
                percent1='%s',
                operator2=operator,
                percent2='%s')
            cr.execute(query, [search_name, search_name])
            ids = list(set([x[0] for x in cr.fetchall()]))
            res_domain = [('id', 'in', ids)]

        return res_domain

    @api.depends()
    def _compute_is_environment_service_provider(self):
        """Compute the value of is_environment_service_provider."""
        service_provider_category = self.env.ref('environment_waste_collect.partner_category_service_provider')

        for rec in self:
            if service_provider_category in rec.category_id:
                rec.is_environment_service_provider = True
            else:
                rec.is_environment_service_provider = False

    def _search_is_environment_service_provider(self, operator, value):
        """Search partner that are service providers.

        :param operator: operator used (= or !=)
        :param value: value used (True or False)
        """
        service_provider_category = self.env.ref('environment_waste_collect.partner_category_service_provider')

        domain = [('category_id', '=', service_provider_category.id)]

        if operator == '=' and not value or operator == '!=' and value:
            domain.insert(expression.NOT_OPERATOR)

        return domain

    @api.depends('subscription_ids')
    def _compute_derogation_count(self):
        package_model = self.env['horanet.package']
        for partner in self:
            derogations = package_model.search([('recipient_id', '=', partner.id), ('is_derogation', '=', True)])
            partner.derogation_count = len(derogations)

    @api.depends()
    def _compute_setup_and_close_wizards_enabled(self):
        environment_config = self.env['horanet.environment.config']
        setup_and_close_wizards_enabled = environment_config.get_enable_setup_and_close_wizards()

        for rec in self:
            rec.setup_and_close_wizards_enabled = setup_and_close_wizards_enabled

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_open_partner_package_derogation(self):
        u"""Return an action that display dérogations for the given partners."""
        action = self.env.ref('horanet_subscription.action_horanet_package').read()[0]
        action['domain'] = ast.literal_eval(action['domain']) if action['domain'] else []
        action['domain'].append(('is_derogation', '=', True))
        action['domain'].append(('recipient_id', 'child_of', self.ids))
        action['name'] = _(u"Dérogations")
        if len(self) == 1:
            action['context'] = ast.literal_eval(action['context'])
            action['context'].update({
                'default_on_create_recipient_id': self.id,
                'default_recipient_id': self.id,
                'package_filter_only_derogation': True,
            })

        return action

    @api.multi
    def action_open_partner_pickup_contract(self):
        action = self.env.ref('environment_waste_collect.pickup_contract_action').read()[0]
        action['name'] = _(u"Pickup contracts")
        if len(self) == 1:
            action['context'] = ast.literal_eval(action['context'])
            action['context'].update({
                'search_default_service_provider_id': self.id,
                'default_service_provider_id': self.id,
            })

        return action
    # endregion

    # region Model methods
    # endregion

    pass
