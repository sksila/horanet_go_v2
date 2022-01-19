# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from odoo.tools import safe_eval
from odoo.addons.environment_production_point.models.partner_move import RESIDENCE_TYPES


class ProductionPointSetUpPartner(models.TransientModel):
    u"""Wizard assistant de création de partner environnement."""

    # region Private attributes
    _inherit = 'partner.setup.wizard'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    old_production_point_id = fields.Many2one(
        string="Production point",
        comodel_name='production.point',
    )
    new_production_point_id = fields.Many2one(
        string="New production point",
        comodel_name='production.point',
    )
    old_residence_type = fields.Selection(
        string='Residence type',
        selection=RESIDENCE_TYPES,
        default='main'
    )
    new_residence_type = fields.Selection(
        string='Residence type',
        selection=RESIDENCE_TYPES,
        default='main'
    )
    partners_production_point_ids = fields.Many2many(
        string="Partner production points",
        comodel_name='production.point',
        compute='_compute_count_partner_production_points')
    count_production_points = fields.Integer(
        string="Production points count",
        compute='_compute_count_partner_production_points')
    new_production_point_ids = fields.Many2many(
        string="New production points",
        comodel_name='production.point',
        compute='_compute_count_new_production_points')
    count_new_production_points = fields.Integer(
        string="New production points count",
        compute='_compute_count_new_production_points')
    create_or_select_production_point = fields.Selection(
        selection=[
            ('modify', 'Modification'),
            ('new', 'Move in'),
            ('move', 'Move in the collectivity'),
        ],
        default='modify')

    production_point_move_ids = fields.One2many(
        string="Moves",
        comodel_name='partner.move',
        related='new_production_point_id.partner_move_ids',
    )

    shown_production_point_move_ids = fields.One2many(
        string="Last moves",
        comodel_name='partner.move',
        compute='_compute_shown_production_point_move_ids',
        readonly=True)

    old_partner_move_id = fields.Many2one(
        string="Partner move",
        comodel_name='partner.move',
        compute='_compute_old_partner_move_id')

    partner_move_id = fields.Many2one(
        string="Partner move",
        comodel_name='partner.move',
        compute='_compute_count_partner_production_points')

    partner_move_ids = fields.One2many(
        string="Moves",
        comodel_name='partner.move',
        related='partner_id.partner_move_ids')

    city_id = fields.Many2one(
        string="City",
        comodel_name='res.city',
        domain="[('country_state_id', '=?', state_id), ('zip_ids.name', '=?', zip)]")

    zip_id = fields.Many2one(string="Zip code", comodel_name='res.zip', domain="[('city_ids', '=?', city_id)]")

    zip = fields.Char(compute='_compute_zip', store=True)

    street_id = fields.Many2one(string="Street", comodel_name='res.street', domain="[('city_id', '=?', city_id)]")

    street2 = fields.Char(string='Additional address')

    street3 = fields.Char(string='Additional address')

    street_number_id = fields.Many2one(string=u"N°", comodel_name='res.street.number')

    city_state_id = fields.Many2one(
        String='City state',
        comodel_name='res.country.state',
        related='city_id.country_state_id',
        readonly=True)

    city_country_id = fields.Many2one(
        String='City state',
        comodel_name='res.country',
        related='city_id.country_id',
        readonly=True)

    country_id = fields.Many2one(string="Country", comodel_name='res.country', domain="[('id', '=?', city_country_id)]")

    state_id = fields.Many2one(string="State", comodel_name='res.country.state', domain="[('id', '=?', city_state_id)]")
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.depends('partner_id', 'production_point_move_ids')
    def _compute_count_partner_production_points(self):
        self.partners_production_point_ids = self.env['partner.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('is_active', '=', True),
        ]).mapped('production_point_id')

        if self.partner_id and self.production_point_move_ids:
            self.partner_move_id = self.production_point_move_ids.filtered(
                lambda r: not r.end_date and r.partner_id == self.partner_id)

        self.count_production_points = len(self.partners_production_point_ids)

    @api.depends('production_point_move_ids', 'new_production_point_ids')
    def _compute_shown_production_point_move_ids(self):
        self.shown_production_point_move_ids = \
            self.production_point_move_ids.sorted('start_date', reverse=True)[0:5]

    @api.onchange('create_or_select_production_point')
    def _onchange_create_or_select_production_point(self):
        if self.create_or_select_production_point == 'move' \
                and self.new_production_point_id == self.old_production_point_id:
            self.zip_id = False
            self.city_id = False
            self.street_number_id = False
            self.street_id = False
            self.street2 = False
            self.street3 = False
            self.state_id = False
            self.country_id = False
            self.new_production_point_id = False

    @api.multi
    @api.depends('zip_id.name', )
    def _compute_zip(self):
        for rec in self:
            rec.zip = rec.zip_id and rec.zip_id.name or False

    @api.onchange('zip_id', )
    def _onchange_zip_id(self):
        if self.new_production_point_id and self.new_production_point_id == self.old_production_point_id:
            self.city_id = False
            self.street_id = False
            self.street_number_id = False

    @api.depends('create_or_select_production_point', 'new_production_point_id',
                 'city_id', 'street_number_id', 'street_id', 'street2', 'street3', 'state_id', 'country_id')
    def _compute_count_new_production_points(self):
        if self.create_or_select_production_point == 'new' or self.create_or_select_production_point == 'move':
            self.new_production_point_ids = self.new_production_point_id.search([
                # ('zip_id', '=?', self.zip_id.id),
                ('city_id', '=?', self.city_id.id),
                ('street_number_id', '=?', self.street_number_id.id),
                ('street_id', '=?', self.street_id.id),
                ('street2', '=?', self.street2 or False),
                ('street3', '=?', self.street3 or False),
                ('state_id', '=?', self.state_id.id),
                ('country_id', '=?', self.country_id.id),
            ])

            self.count_new_production_points = len(self.new_production_point_ids)

    @api.depends('old_production_point_id')
    def _compute_old_partner_move_id(self):
        for rec in self:
            rec.old_partner_move_id = rec.old_production_point_id.partner_move_ids.filtered(
                lambda move: move.partner_id == rec.partner_id).sorted('start_date', reverse=True)[0]

    @api.onchange('old_production_point_id')
    def _onchange_old_production_point_id(self):
        # On force le nouveau point à l'ancien, même s'il est vide
        if self.create_or_select_production_point == 'modify':
            self.new_production_point_id = self.old_production_point_id
            self.partner_move_id = self.production_point_move_ids.filtered(
                lambda r: not r.end_date and r.partner_id == self.partner_id)
            self.old_residence_type = self.partner_move_id.residence_type

    @api.onchange('create_or_select_production_point', 'old_production_point_id',
                  'city_id', 'street_number_id', 'street_id', 'street2', 'street3', 'state_id', 'country_id')
    def _on_change_create_or_select_production_point(self):
        if self.create_or_select_production_point == 'modify':
            self.new_production_point_id = self.old_production_point_id

        if self.create_or_select_production_point == 'modify' or self.create_or_select_production_point == 'move':
            if self.count_production_points == 0:
                self.create_or_select_production_point = 'new'
            else:
                if self.count_production_points == 1:

                    partner_old_production_point = self.env['partner.move'].search([
                        ('partner_id', '=', self.partner_id.id),
                        ('end_date', '=', self.env.context.get('default_new_situation_date'))]).mapped(
                        'production_point_id')

                    self.old_production_point_id = partner_old_production_point[0] if \
                        partner_old_production_point else self.partners_production_point_ids[0]

                    if self.create_or_select_production_point == 'modify':
                        self.new_production_point_id = self.old_production_point_id

                if self.create_or_select_production_point == 'modify':
                    return {
                        'domain': {'old_production_point_id': [('id', 'in', self.partners_production_point_ids.ids)]},
                    }

        if self.create_or_select_production_point == 'new' or self.create_or_select_production_point == 'move':
            if self.count_new_production_points == 1 \
                    and self.new_production_point_ids[0] != self.old_production_point_id:
                self.new_production_point_id = self.new_production_point_ids[0]

            return {
                'domain': {
                    'new_production_point_id': [
                        ('id', 'in', self.new_production_point_ids.ids),
                        ('id', 'not in', [self.old_production_point_id.id]),
                    ],
                    'old_production_point_id': [('id', 'in', self.partners_production_point_ids.ids)]
                }
            }

    # endregion

    # region CRUD (overrides)
    @api.depends('partner_id', 'partner_move_id')
    def compute_tag_ids(self):
        u"""Surcharge pour ajouter aux tags pointant vers un partner, les tags d'eménagements."""
        self.ensure_one()
        assignation_model = self.env['partner.contact.identification.assignation']
        context_date = self.new_situation_date
        active_assignation_domain = assignation_model.search_is_active('=', True, context_date)

        if self.partner_move_id and not self.tag_ids:
            move_assignation_ids = assignation_model.search(
                active_assignation_domain + [('move_id', '=', self.partner_move_id.id)])
            self.tag_ids = [(6, 0, move_assignation_ids.mapped('tag_id.id'))]

    # endregion

    # region Actions

    def action_next_stage(self):
        self.ensure_one()

        if self.env.context.get('current_stage') == self.env.ref(
                'environment_production_point.wizard_stage_production_point_attribution').id:

            # Point de production obligatoire
            if not self.new_production_point_id:
                raise ValidationError(_("You must select or create a production point to continue"))

            if self.create_or_select_production_point == 'new' or self.create_or_select_production_point == 'move':
                # Type de résidence obligatoire
                if not self.new_residence_type:
                    raise ValidationError(_("You must select residence type"))

                active_moves = self.production_point_move_ids.filtered('is_active')

                icp_model = self.env['ir.config_parameter']

                allow_multiple_moves_on_same_production_point = safe_eval(
                    icp_model.get_param('environment_production_point.allow_multiple_moves_on_same_production_point',
                                        'False'))

                if allow_multiple_moves_on_same_production_point:
                    # Il ne peut pas y avoir plusieurs emménagements actifs pour le même producteur
                    # sur un point de production
                    active_moves = active_moves.filtered(lambda m: m.partner_id == self.partner_id)

                # S'il y a déjà un emménagment actif, on bloque
                if active_moves:
                    raise ValidationError(
                        _("There is a current move on this production point"))

                #  S'il n'y en a pas, on le créée
                self.env['partner.move'].create({
                    'production_point_id': self.new_production_point_id.id,
                    'partner_id': self.partner_id.id,
                    'residence_type': self.new_residence_type,
                    'start_date': self.new_situation_date
                })

                if self.create_or_select_production_point == 'move':
                    # On met fin à l'emménagement du producteur sur son ancien point de production
                    self.end_old_partner_move()

        return super(ProductionPointSetUpPartner, self).action_next_stage()

    def action_create_production_point(self):
        """Redefine function to enroll medium on partner move instead of partner."""
        self.ensure_one()

        # Création d'un nouveau point de production
        self.new_production_point_id = self.new_production_point_id.create({
            'zip_id': self.zip_id.id,
            'city_id': self.city_id.id,
            'street_number_id': self.street_number_id.id,
            'street_id': self.street_id.id,
            'street2': self.street2,
            'street3': self.street3,
            'state_id': self.state_id.id,
            'country_id': self.country_id.id
        })

        self.new_production_point_id.name = self.new_production_point_id.display_address

        return self._self_refresh_wizard()

    def action_create_another_production_point(self):
        self.ensure_one()

        self.stage_id = self.env.ref(
            'environment_production_point.wizard_stage_production_point_attribution').id
        self.create_or_select_production_point = 'new'

        return self._self_refresh_wizard()

    def action_move_old_production_point_tags(self, refresh=True, old_assignations=False, partner_move_id=False):
        self.ensure_one()

        old_assignations = old_assignations or self.env['partner.contact.identification.assignation'].search([
            ('reference_id', '=', 'partner.move,%d' % self.old_partner_move_id.id),
            ('end_date', '=', False),
        ])

        # On met fin aux dotations de l'ancien emménagement
        old_assignations.write({
            'end_date': fields.Datetime.from_string(self.new_situation_date) - timedelta(seconds=1)
        })

        #  Pour chaque dotation de l'ancien emménagement
        for old_assignation in old_assignations:
            # On créée une nouvelle dotation sur le nouvel emménagement
            self.env['partner.contact.identification.assignation'].create({
                'reference_id': 'partner.move,%d' % (
                    partner_move_id.id if partner_move_id else self.partner_move_id.id),
                'start_date': self.new_situation_date,
                'tag_id': old_assignation.tag_id.id,
            })

        if refresh:
            return self._self_refresh_wizard()

    def action_change_old_residence_type(self):

        old_assignations = self.env['partner.contact.identification.assignation'].search([
            ('reference_id', '=', 'partner.move,%d' % self.old_partner_move_id.id),
            ('end_date', '=', False),
        ])

        self.partner_move_id.write({
            'end_date': fields.Datetime.from_string(self.new_situation_date) - timedelta(seconds=1)
        })

        residence_type = RESIDENCE_TYPES[0][0]
        if self.partner_move_id.residence_type == residence_type:
            residence_type = RESIDENCE_TYPES[1][0]

        self.old_partner_move_id = self.env['partner.move'].create({
            'production_point_id': self.new_production_point_id.id,
            'partner_id': self.partner_id.id,
            'residence_type': residence_type,
            'start_date': self.new_situation_date
        })

        self.action_move_old_production_point_tags(False, old_assignations, partner_move_id=self.old_partner_move_id)

        return self._self_refresh_wizard()

    # endregion

    # region Model methods
    def next_stage(self):
        if self.env.context.get('current_stage') == self.env.ref(
                'environment_waste_collect.wizard_stage_subscription_template_choice').id:

            if self.subscription_id and self.subscription_id != self.partner_move_id.subscription_id:
                self.partner_move_id.subscription_id = self.subscription_id

        return super(ProductionPointSetUpPartner, self).next_stage()

    def action_enroll_medium(self):
        """Redefine function to enroll medium on partner move instead of partner."""
        self.ensure_one()

        self.env['partner.contact.identification.wizard.create.medium'].with_context({
            'default_reference_id': self.partner_move_id.id,
            'model_name': 'partner.move',
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
            self.env['partner.contact.identification.wizard.create.medium'].create_assignation(
                self.env.context.get('tag_id'), 'partner.move', self.partner_move_id.id)

        return self._self_refresh_wizard()

    def end_old_partner_move(self):
        self.old_partner_move_id.end_date = self.new_situation_date
        # on fait suivre les tags
        self.action_move_old_production_point_tags(refresh=False)

    # endregion

    pass
