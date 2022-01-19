
from odoo import api, fields, models, _
from odoo.tools import safe_eval
from odoo.exceptions import ValidationError
try:
    from odoo.addons.horanet_go.tools.utils import format_log

except ImportError:
    from horanet_go.tools.utils import format_log


class SetUpPartner(models.TransientModel):
    u"""Wizard assistant de création de partner environnement."""

    # region Private attributes
    _name = 'partner.setup.wizard'

    # endregion

    # region Default methods
    def _get_default_mapping(self):
        return safe_eval(self.env['ir.config_parameter'].get_param(
            'partner_contact_identification.default_mapping_id', 'False'
        ))

    def _get_default_stage(self):
        return self.env['partner.setup.wizard.stage'].search([], order='order', limit=1)

    # endregion

    # region Fields declaration
    stage_id = fields.Many2one(string="Stage",
                               comodel_name='partner.setup.wizard.stage',
                               default=_get_default_stage)

    is_min_stage = fields.Boolean(string="Is minimum stage", compute='_compute_min_max_stages')

    is_max_stage = fields.Boolean(string="Is maximum stage", compute='_compute_min_max_stages')

    max_validated_stage_id = fields.Many2one(string="Maximum validated stage",
                                             comodel_name='partner.setup.wizard.stage')

    is_validated_stage = fields.Boolean(string="Is maximum validated stage",
                                        compute='_compute_is_validated_stage')

    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner', required=True, delete='cascade')

    new_situation_date = fields.Datetime(default=fields.Datetime.now, required=True)

    # Mediums
    mapping_id = fields.Many2one(
        string="Mapping",
        comodel_name='partner.contact.identification.mapping',
        default=lambda self: self._get_default_mapping(),
        domain="[('mapping', '=', 'csn')]",
        readonly=True
    )
    max_length = fields.Integer(related='mapping_id.max_length', readonly=True)
    mapping = fields.Selection(related='mapping_id.mapping', readonly=True)
    csn_number = fields.Char(string="CSN Number")

    tag_id = fields.Many2one(
        string='Tag',
        comodel_name='partner.contact.identification.tag',
        domain="[('is_assigned', '=', False),"
               " ('number', '=?', csn_number),"
               " ('mapping_id', '=', mapping_id),"
               "]",
    )

    tag_ids = fields.Many2many(
        string='Tag list',
        comodel_name='partner.contact.identification.tag',
        compute="compute_tag_ids",
        readonly=True,
    )

    # Subscriptions
    create_or_select_subscription = fields.Selection(
        selection=[('existing', 'Select existing subscription'), ('new', 'Create new subscription')],
        default='existing')

    partner_subscription_template_ids = fields.Many2many(
        string="Partner subscription templates",
        comodel_name='horanet.subscription.template',
        compute='_compute_count_partner_subscriptions',
    )

    subscription_template_id = fields.Many2one(
        string="Subscription template",
        comodel_name='horanet.subscription.template',
    )

    count_subscription_templates = fields.Integer(
        string="Subscription templates count",
        compute='_compute_count_partner_subscriptions',
    )

    add_or_remove_fixed_part = fields.Selection(
        selection=[
            ('add', 'Add'),
            ('remove', 'Remove'),
        ],
        default='add'
    )

    subscription_fixed_part_ids = fields.Many2many(
        string="Fixed parts",
        comodel_name='horanet.package',
        compute='_compute_subscription_fixed_part_ids',
        readonly=True
    )

    active_subscription_fixed_part_ids = fields.Many2many(
        string="Fixed parts",
        comodel_name='horanet.package',
        compute='_compute_subscription_fixed_part_ids',
        readonly=True
    )

    fixed_part_prestation_id = fields.Many2one(
        string="Fixed part",
        comodel_name="horanet.prestation",
    )

    fixed_part_exoneration = fields.Boolean(string="Fixed part exoneration")

    partner_subscription_ids = fields.Many2many(
        string="Partner subscriptions",
        comodel_name='horanet.subscription',
        compute='_compute_count_partner_subscriptions',
    )

    subscription_id = fields.Many2one(
        string="Contract",
        comodel_name='horanet.subscription',
        domain="[('client_id', '=', partner_id),"
               "('subscription_template_id.prestation_ids.activity_ids.application_type', '=', 'environment'),"
               "('state', '=', 'active')]"
    )

    subscription_name = fields.Char(related="subscription_id.name")

    count_subscriptions = fields.Integer(
        string="Subscriptions count",
        compute='_compute_count_partner_subscriptions',
    )

    message_box = fields.Text(
        string="Display message",
        compute='_compute_message_box',
        store=False)

    # endregion

    # region Fields method
    @api.depends('stage_id')
    def _compute_min_max_stages(self):
        min_stage = self.env['partner.setup.wizard.stage'].search([], order='order asc', limit=1)
        if self.stage_id == min_stage:
            self.is_min_stage = True
        else:
            self.is_min_stage = False

        max_stage = self.env['partner.setup.wizard.stage'].search([], order='order desc', limit=1)
        if self.stage_id == max_stage:
            self.is_max_stage = True
        else:
            self.is_max_stage = False

    @api.depends('stage_id', 'max_validated_stage_id')
    def _compute_is_validated_stage(self):
        if self.max_validated_stage_id:
            self.is_validated_stage = self.stage_id.order <= self.max_validated_stage_id.order

    @api.depends('create_or_select_subscription')
    def _compute_message_box(self):
        self.ensure_one()

        message = ''
        partner_active_contract = self.env['horanet.subscription'].search([
            '|',
            '|',
            ('state', '=', 'active'), ('state', '=', 'pending'),
            '|',
            ('state', '=', 'draft'), ('state', '=', 'to_compute'),
            ('client_id', '=', self.partner_id.id),
            ('subscription_template_id.prestation_ids.activity_ids.application_type', '=', 'environment'),
            '|',
            ('closing_date', '=', False), ('closing_date', '>', fields.Date.context_today(self))

        ])

        if self.create_or_select_subscription == 'new' and partner_active_contract:
            message += u"<b><warning>{title}</warning></b>:\n\t{message}\n".format(
                title=_("Remark"),
                message=_("This partners already have an active, a pending or a new subscription for this "
                          "subscription template. If you don't want to attribute another subscription "
                          "select 'Select existing subscription' or remove the existing subscription before."))

        self.message_box = message and format_log(message) or False

    # endregion

    # region Constrains and Onchange
    @api.onchange('partner_id')
    def _compute_count_partner_subscriptions(self):
        self.partner_subscription_ids = self.env['horanet.subscription'].search([
            ('client_id', '=', self.partner_id.id),
            ('subscription_template_id.prestation_ids.activity_ids.application_type', '=', 'environment'),
            ('state', '=', 'active')
        ])

        self.count_subscriptions = len(self.partner_subscription_ids)

        self.partner_subscription_template_ids = self.env['horanet.subscription.template'].search([
            ('prestation_ids.activity_ids.application_type', '=', 'environment'),
            ('subscription_category_ids', 'in', self.partner_id.subscription_category_ids.ids)
        ])

        self.count_subscription_templates = len(self.partner_subscription_template_ids)

    @api.onchange('create_or_select_subscription')
    def _on_change_create_or_select_subscription(self):
        if self.create_or_select_subscription == 'existing':
            if self.count_subscriptions == 0:
                self.create_or_select_subscription = 'new'
            else:
                if self.count_subscriptions == 1:
                    self.subscription_id = self.partner_subscription_ids[0]
                else:
                    self.subscription_template_id = False

                return {
                    'domain': {'subscription_id': [('id', 'in', self.partner_subscription_ids.ids)]},
                }

        if self.create_or_select_subscription == 'new':
            self.subscription_id = False

            if self.count_subscription_templates == 1:
                self.subscription_template_id = self.partner_subscription_template_ids[0]
            else:
                self.subscription_template_id = False

            return {
                'domain': {'subscription_template_id': [('id', 'in', self.partner_subscription_template_ids.ids)]},
            }

    @api.onchange('subscription_id')
    def _on_change_subscription_id(self):
        if self.create_or_select_subscription == 'existing' and self.subscription_id:
            self.subscription_template_id = self.subscription_id.subscription_template_id

    @api.onchange('add_or_remove_fixed_part', 'subscription_fixed_part_ids')
    def _compute_possible_fixed_part_prestation_ids(self):
        # Filtrage des prestations de part fixe en fonction de la categorie de l'usager
        self.fixed_part_prestation_id = False
        if self.add_or_remove_fixed_part == 'add':
            possible_fixed_part_prestation_ids = self.env['horanet.prestation'].search([
                ('use_product', '=', True),
            ]).filtered(lambda p: not p.subscription_category_ids
                        or p.subscription_category_ids & self.partner_id.mapped('subscription_category_ids'))
            if len(possible_fixed_part_prestation_ids) == 0:
                self.fixed_part_exoneration = True
        else:
            possible_fixed_part_prestation_ids = self.active_subscription_fixed_part_ids.mapped('prestation_id')

        return {
            'domain': {'fixed_part_prestation_id': [('id', 'in', possible_fixed_part_prestation_ids.ids)]},
        }

    @api.depends('subscription_id')
    def _compute_subscription_fixed_part_ids(self):
        if self.subscription_id:
            fixed_part_ids = self.subscription_id.package_ids.filtered(
                lambda p: p.use_product).sorted('opening_date', reverse=True)
            self.active_subscription_fixed_part_ids = fixed_part_ids.search([
                ('id', 'in', fixed_part_ids.ids),
                ('state', '=', 'active'),
            ])
            self.subscription_fixed_part_ids = fixed_part_ids[0:5]

    @api.depends('partner_id')
    def compute_tag_ids(self):
        for rec in self:
            rec.tag_ids = rec.partner_id.tag_ids

    @api.onchange('mapping_id', 'csn_number')
    def _onchange_waste_site_medium_infos(self):
        self.possible_tag_ids = self.env['partner.contact.identification.tag'].search([
            ('is_assigned', '=', False),
            ('number', '=', self.csn_number),
            ('mapping_id', '=', self.mapping_id.id),
        ])
        if len(self.possible_tag_ids) == 1:
            self.tag_id = self.possible_tag_ids[0]
        else:
            self.tag_id = False

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_previous_stage(self):
        self.ensure_one()

        previous_stage = self.env['partner.setup.wizard.stage'].search(
            [('order', '<', self.stage_id.order)], order='order desc', limit=1)

        self.stage_id = previous_stage.id
        return self._self_refresh_wizard(stage_modified=False)

    def action_next_stage(self):
        self.ensure_one()

        if self.partner_id:
            if self.env.context.get('current_stage') == self.env.ref(
                    'environment_waste_collect.wizard_stage_subscription_template_choice').id:
                # Partie subscription
                if self.create_or_select_subscription == 'new':
                    if not self.subscription_template_id:
                        raise ValidationError(_("You must select a subscription template to continue"))

                    self.subscription_id = \
                        self.env['horanet.subscription'].create_subscription(
                            [self.partner_id.id], self.subscription_template_id.id, fields.Date.context_today(self),
                            prorata_temporis=True, confirmation=True
                        )

                if not self.subscription_id:
                    raise ValidationError(_("You must select a subscription to continue"))

                self.subscription_template_id = self.subscription_id.subscription_template_id
                self.create_or_select_subscription = 'existing'

                self.csn_number = False
                self.tag_id = False

            if self.env.context.get('current_stage') == self.env.ref(
                    'environment_waste_collect.wizard_stage_fixed_part_choice').id:

                if not self.fixed_part_exoneration and not self.active_subscription_fixed_part_ids:
                    raise ValidationError(_("You must add a fixed part or check exoneration box"))

            self.max_validated_stage_id = self.stage_id
            return self.next_stage()

    @api.multi
    def _self_refresh_wizard(self, stage_modified=True):
        self.ensure_one()

        if stage_modified:
            previous_stage = self.env['partner.setup.wizard.stage'].search(
                [('order', '<', self.stage_id.order)], order='order desc', limit=1)
            self.max_validated_stage_id = previous_stage

        context = self.env.context.copy()
        for field_name in self._fields:
            if self._fields[field_name] \
                    and not isinstance(self._fields[field_name], (fields.One2many, fields.Many2many)) \
                    and not self._fields[field_name].compute:
                value = self[field_name]
                if isinstance(self._fields[field_name], fields.Many2one):
                    value = self[field_name].id

                context.update({
                    'default_' + field_name: value
                })

        # Rappel du wizard en gardant son contexte
        return {
            'name': self.stage_id.name,
            'context': context,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            # 'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.stage_id.view_id.id,
            'target': 'new',
        }

    def action_enroll_medium(self):
        self.ensure_one()

        self.env['partner.contact.identification.wizard.create.medium'].with_context({
            'default_reference_id': self.partner_id.id,
        }).create({
            'mapping_id': self.env.context.get('mapping_id'),
            'csn_number': self.env.context.get('csn_number'),
        }).action_enroll_medium()

        return self._self_refresh_wizard()

    def action_move_tag(self):
        self.ensure_one()
        # Partie bacs
        if self.env.context.get('tag_id'):
            # On crée une assignation
            self.env['partner.contact.identification.wizard.create.medium'] \
                .create_assignation(self.env.context.get('tag_id'), 'res.partner', self.partner_id.id)

        return self._self_refresh_wizard()

    def action_add_or_remove_fixed_part(self):
        u"""
        Ajout de la part fixe sélectionnée.

        On rajoute une ligne de contrat de part fixe au contrat en fonction de la prestation sélectionnée.
        :return:
        """
        self.ensure_one()

        # Erreur part fixe non sélectionnée
        if not self.fixed_part_prestation_id:
            raise ValidationError(_("Select a fixed part"))

        if self.add_or_remove_fixed_part == 'add':
            # On crée une ligne de contrat avec la part fixe
            package = self.env['horanet.package'].create_package(
                self.fixed_part_prestation_id,
                self.subscription_id,
                self.new_situation_date,
                prorata_temporis=True
            )

            package.compute_package()
        else:
            # On met fin à la ligne de contrat correspondante
            self.active_subscription_fixed_part_ids.filtered(
                lambda p: p.prestation_id == self.fixed_part_prestation_id
            )[0].update_active_period(
                closing_date=self.new_situation_date,
                prorata=True
            )

        return self._self_refresh_wizard()

    # endregion

    # region Model methods
    def next_stage(self):

        next_stage_id = self.env['partner.setup.wizard.stage'].search(
            [('order', '>', self.stage_id.order)], order='order asc', limit=1).id

        self.stage_id = next_stage_id
        return self._self_refresh_wizard(stage_modified=False)

    # endregion

    pass
