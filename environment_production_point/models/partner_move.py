# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions, _
from odoo.osv import expression
from odoo.tools import safe_eval
from datetime import datetime, date

RESIDENCE_TYPES = [('main', 'Main residence'),
                   ('secondary', 'Secondary residence')]


class PartnerMove(models.Model):
    # region Private attributes
    _name = 'partner.move'
    _rec_name = 'name'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name",
        compute='_compute_move_name',
        store=False,
    )
    production_point_id = fields.Many2one(
        string="Production point",
        comodel_name='production.point',
        required=True
    )

    partner_id = fields.Many2one(
        string="Producer",
        comodel_name='res.partner',
        required=True,
        index=True,
        domain="[('company_type', '!=', 'foyer')]",
    )

    subscription_id = fields.Many2one(
        string="Subscription",
        comodel_name='horanet.subscription'
    )

    residence_type = fields.Selection(
        string='Residence type',
        selection=RESIDENCE_TYPES,
        required=True,
        default='main'
    )
    assignation_ids = fields.One2many(
        string='Assignations',
        comodel_name='partner.contact.identification.assignation',
        inverse_name='move_id',
    )
    tag_ids = fields.Many2many(
        string='Tags',
        comodel_name='partner.contact.identification.tag',
        compute='_compute_move_tags',
        store=False,
    )

    start_date = fields.Datetime(required=True, default=fields.Datetime.now)
    end_date = fields.Datetime()
    is_active = fields.Boolean(
        string="Is active",
        compute='_compute_is_active',
        search='search_is_active')

    # endregion

    # region Fields method
    @api.depends('partner_id.name', 'production_point_id')
    def _compute_move_name(self):
        """Compute mediums of a partner."""
        for move in self:
            move.name = move.partner_id.name + ' ' + move.production_point_id.name

    @api.depends()
    def _compute_move_tags(self):
        """Compute mediums of a partner."""
        for move in self:
            move.tag_ids = move.assignation_ids.filtered('is_active').mapped('tag_id')

    @api.depends('start_date', 'end_date')
    def _compute_is_active(self):
        """Compute the active property of the move at the current date."""
        search_date = fields.Datetime.now()

        for move in self:
            if move.end_date:
                move.is_active = move.start_date <= search_date < move.end_date
            else:
                move.is_active = move.start_date <= search_date

    def search_is_active(self, operator, value, search_date=False):
        """Determine the domain used to search allocation by is_active value.

        :param operator: the search operator
        :param value: Boolean False or True
        :param search_date: optional, the date at which the search must be performed
        :return: A search domain
        """
        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        search_date_time = search_date or self.env.context.get('force_time', fields.Datetime.now())

        if isinstance(search_date_time, (datetime, date)):
            search_date_time = fields.Datetime.to_string(search_date_time)
        elif isinstance(search_date_time, basestring):
            search_date_time = fields.Datetime.to_string(fields.Datetime.from_string(search_date_time))
        else:
            raise ValueError('search_date_utc must be an Odoo date (str) or date object')

        domain = [
            '&',
            ('start_date', '<=', search_date_time),
            '|',
            ('end_date', '=', False), ('end_date', '>=', search_date_time)
        ]

        if (value and operator == '!=') or (not value and operator == '='):
            domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(domain)

    def name_get(self):
        names = []

        for rec in self:
            name = rec.partner_id.name + ' ' + rec.production_point_id.name
            names.append((rec.id, name))

        return names
    # endregion

    # region Constrains and Onchange
    @api.constrains('start_date', 'end_date')
    def _check_date_consistency(self):
        for rec in self:
            if not rec.end_date:
                continue

            if rec.end_date < rec.start_date:
                raise exceptions.ValidationError(_("End date should be posterior or equal to start date."))

    @api.constrains('production_point_id', 'partner_id', 'start_date', 'end_date')
    def _check_unicity(self):
        """Check if there is an ongoing move for the production point."""
        icp_model = self.env['ir.config_parameter']

        allow_multiple_moves_on_same_production_point = safe_eval(
            icp_model.get_param('environment_production_point.allow_multiple_moves_on_same_production_point',
                                'False'))

        if allow_multiple_moves_on_same_production_point:
            return

        for rec in self:
            moves = self.search([
                ('production_point_id', '=', rec.production_point_id.id),
                ('id', '!=', rec.id)
            ])

            for move in moves:
                if (not rec.end_date and rec.start_date <= move.start_date) or \
                 (rec.end_date and rec.start_date <= move.start_date <= rec.end_date) or \
                 (not move.end_date and move.start_date <= rec.start_date) or \
                 (move.end_date and move.start_date <= rec.start_date <= move.end_date):
                    raise exceptions.ValidationError(_("There is already a partner "
                                                       "at this production point for the provided dates"))
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
    pass
