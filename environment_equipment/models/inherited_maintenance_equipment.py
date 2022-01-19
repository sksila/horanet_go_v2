# -*- coding: utf-8 -*-

import calendar
import logging
from datetime import datetime, date

from odoo import models, fields, api, _, exceptions
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class InheritedEquipment(models.Model):
    # region Private attributes
    _inherit = 'maintenance.equipment'
    _sql_constraints = [
        ('chip_number_and_tub_number',
         'UNIQUE(chip_number, tub_number)',
         _("The chip number and tub number combination must be unique")),
    ]

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(required=True, translate=False, compute='_compute_equipment_name',
                       search='_search_equipment_by_name')

    move_id = fields.Many2one(
        string="Partner move",
        comodel_name='partner.move',
        compute='_compute_move_id',
        store=False
    )
    owner_partner_id = fields.Many2one(
        string="Producer",
        comodel_name='res.partner',
        compute='_compute_owner_partner_id',
        search='search_owner_partner_id',
        store=False,
    )
    production_point_id = fields.Many2one(
        string="Production point",
        comodel_name='production.point',
        compute='_compute_production_point_id',
        search='search_production_point_id',
        store=False,
    )
    category_id = fields.Many2one(string="Equipment category")
    use_product = fields.Boolean(string="Use product")
    product_id = fields.Many2one(string="Product", comodel_name='product.template')
    chip_number = fields.Char(string="Chip number", required=False)
    capacity = fields.Integer(sring="Capacity")
    capacity_unit_id = fields.Many2one(string="Capacity unit", comodel_name='product.uom')
    tub_number = fields.Char(string="Tub number")
    operation_ids = fields.One2many(
        string="Pickups",
        comodel_name='horanet.operation',
        inverse_name='maintenance_equipment_id'
    )

    has_alert = fields.Boolean(
        string="Has alert",
        compute='_compute_equipment_alert',
        store=True)
    alert = fields.Text(
        string="Notes about pickups",
        compute='_compute_equipment_alert',
        readonly=True,
        translate=True
    )

    allocation_ids = fields.One2many(
        string="Allocations",
        comodel_name='partner.move.equipment.rel',
        inverse_name='equipment_id'
    )

    status_id = fields.Many2one(string="Status", comodel_name='equipment.status', track_visibility='always')

    # endregion

    # region Fields method
    @api.depends()
    def _compute_move_id(self):
        for equipment in self:
            equipment.move_id = equipment.get_equipment_move()

    @api.depends('move_id')
    def _compute_owner_partner_id(self):
        for equipment in self:
            equipment.owner_partner_id = equipment.move_id and equipment.move_id.partner_id or False

    @api.depends('move_id')
    def _compute_production_point_id(self):
        for equipment in self:
            equipment.production_point_id = equipment.move_id and equipment.move_id.production_point_id or False

    @api.depends()
    def _compute_equipment_alert(self):
        """Write a note about the pickups."""
        for rec in self:
            if not rec.operation_ids or not rec.production_point_id:
                continue

            list_alert_message = []
            # On va chercher si il y a d'autres bacs du même type dans la même rue
            other_equipments = self.search([
                ('category_id', '=', rec.category_id.id),
                ('production_point_id.street_id', '=', rec.production_point_id.street_id.id),
                ('production_point_id.city_id', '=', rec.production_point_id.city_id.id),
                ('production_point_id.zip_id', '=', rec.production_point_id.zip_id.id)
            ])

            if not other_equipments:
                continue

            # 1 - Une alerte pour si le bac n'a pas été relevé
            # On va chercher la dernière relève
            last_pickup = rec.operation_ids.search([('maintenance_equipment_id', 'in', other_equipments.ids)],
                                                   order='time desc', limit=1)
            if last_pickup:
                date_begin = datetime.strptime(last_pickup.time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d 00:00:00')
                date_end = datetime.strptime(last_pickup.time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d 23:59:59')
                # On va chercher si il y a des relèves effectuées le même jour que les autre
                same_day_pickups = rec.operation_ids.search([('maintenance_equipment_id', '=', rec.id),
                                                             ('time', '>=', date_begin), ('time', '<=', date_end)],
                                                            order='time desc')
                # Si il n'y en a pas, alors on met une alerte
                if not same_day_pickups:
                    list_alert_message.append(_("This container has not been picked up during the "
                                                "last picking on {}.".format(last_pickup.time)))
            # 2 - Une alerte pour la moyenne des relevés mensuels
            date_begin = datetime.strftime(datetime.now().date(), '%Y-%m-01 00:00:00')
            last_day = calendar.monthrange(datetime.now().date().year, datetime.now().date().month)
            date_end = datetime.strftime(datetime.now().date(), '%Y-%m-' + str(last_day[1]) + ' 00:00:00')
            pickups_month = rec.operation_ids.search([('maintenance_equipment_id', 'in', other_equipments.ids),
                                                      ('time', '>=', date_begin),
                                                      ('time', '<=', date_end)],
                                                     order='time desc')
            # Relèves de ce bac ce mois-ci
            this_pickups_month = rec.operation_ids.search(
                [('maintenance_equipment_id', '=', rec.id),
                 ('time', '>=', date_begin), ('time', '<=', date_end)], order='time desc')

            # Moyennes pour les autres bacs et celui-ci
            average = len(pickups_month) / len(other_equipments)
            this_average = len(this_pickups_month)

            if this_average > average:
                list_alert_message.append(_("The monthly average number of pickups on this container ({}) is "
                                            "higher than the average of the "
                                            "others ({}).".format(this_average, average)))

            if list_alert_message:
                rec.has_alert = True
                rec.alert = ('\n'.join(list_alert_message) + '\n')
            else:
                rec.has_alert = False

    def search_owner_partner_id(self, operator, value, search_date=False):
        """Search equipment (active) for a partner.

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

        if not isinstance(value, int) and not isinstance(value, list):
            raise TypeError("Search equipments: Expected integer or list of integer, found {bad_type}".format(
                bad_type=str(type(value)))
            )

        if isinstance(value, int):
            value = [value]

        move_model = self.env['partner.move']
        move_active_domain = move_model.search_is_active('=', True, search_date=search_date_time)
        move_partner = move_model.search([('partner_id', 'in', value)] + move_active_domain)

        allocation_model = self.env['partner.move.equipment.rel']
        allocation_active_domain = allocation_model.search_is_active('=', True, search_date=search_date_time)

        allocation_partner = allocation_model.search([('move_id', 'in', move_partner.ids)] + allocation_active_domain)
        equipment_ids = allocation_partner and allocation_partner.mapped('equipment_id.id')

        domain = [('id', 'in', equipment_ids or [])]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(domain)

    def search_production_point_id(self, operator, value, search_date=False):
        """Search equipment (active) for a production_point.

        :param operator: the search operator
        :param value: boolean, string, record id or list of record ids
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

        if isinstance(value, bool):
            if not value and operator == '!=':
                operator = '='
            elif not value and operator == '=':
                operator = '!='
            op = '!='
            value = False
        elif isinstance(value, int):
            value = [value]
            op = 'in'
        elif isinstance(value, list):
            op = 'in'
        elif isinstance(value, unicode):
            op = 'ilike'
        else:
            raise TypeError("Search equipments: Expected int, list of int, str or bool, found {bad_type}".format(
                bad_type=str(type(value)))
            )

        move_model = self.env['partner.move']
        move_active_domain = move_model.search_is_active('=', True, search_date=search_date_time)
        move_ppoint = move_model.search([('production_point_id', op, value)] + move_active_domain)

        allocation_model = self.env['partner.move.equipment.rel']
        allocation_active_domain = allocation_model.search_is_active('=', True, search_date=search_date_time)

        allocation_partner = allocation_model.search([('move_id', 'in', move_ppoint.ids)] + allocation_active_domain)
        equipment_ids = allocation_partner and allocation_partner.mapped('equipment_id.id')

        domain = [('id', 'in', equipment_ids or [])]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(domain)

    @api.depends('category_id', 'owner_partner_id', 'chip_number', 'tub_number')
    def _compute_equipment_name(self):
        """Compute the name of the equipment."""
        for rec in self:
            prefix = rec.category_id.name or ''

            if rec.owner_partner_id:
                prefix += ", %s" % rec.owner_partner_id.name

            if rec.chip_number or rec.tub_number:
                prefix += ', %s %s' % (rec.chip_number or '', rec.tub_number or '')

            rec.name = prefix or 'Unknown'

    def _search_equipment_by_name(self, operator, value):
        """
        Search the equipment by the specified name.

        :param operator: operator
        :param value: value
        :return: domain
        """
        # TODO : gérer les négations et les recherche partielles (ex : qui commence par )
        # seearch_domain = expression.FALSE_DOMAIN

        # Vérification de l'opérateur
        if operator not in ['=', '!=', '=like', '=ilike', 'like', 'not like', 'ilike', 'not ilike']:
            return expression.FALSE_DOMAIN

        if not isinstance(value, basestring):
            return expression.FALSE_DOMAIN

        if not value:
            return expression.TRUE_DOMAIN

        search_domain = expression.OR([
            [('owner_partner_id.name', operator, value)],
            [('chip_number', operator, value)],
            [('tub_number', operator, value)]
        ])

        # if operator in expression.NEGATIVE_TERM_OPERATORS:
        #     domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(search_domain)

    # endregion

    # region Constrains and Onchange
    @api.onchange('category_id')
    def _onchange_category_id(self):
        """Use the properties of the equipment category on the equipment."""
        if self.category_id:
            self.use_product = self.category_id.use_product
            self.product_id = self.category_id.product_id and self.category_id.product_id.id or False
            self.capacity = self.category_id.capacity
            self.capacity_unit_id = self.category_id.capacity_unit_id and self.category_id.capacity_unit_id.id or False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Use the properties of the product on the equipment."""
        if self.product_id:
            self.bar_code = self.product_id.barcode

    @api.constrains('active')
    def _check_equipment_deactivation(self):
        """Check if we can deactivate an equipment."""
        if self.active is False and self.allocation_ids:
            for allocation_id in self.allocation_ids:
                if allocation_id.is_active:
                    raise exceptions.ValidationError(_("This equipment has an active allocation. "
                                                       "If you want to deactivate this equipment, "
                                                       "put a end to its allocations."))

    # endregion

    # region CRUD (overrides)
    @api.multi
    def _track_subtype(self, init_values):
        """We create a notification if the address is changed."""
        self.ensure_one()
        if 'attribution_type' in init_values and self.production_point_id:
            return 'environment_equipment.mt_address_assign'
        return super(InheritedEquipment, self)._track_subtype(init_values)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_equipment_linked_packages(self, search_time):
        self.ensure_one()
        packages = self.env['horanet.package']
        allocation_model = self.env['partner.move.equipment.rel']
        search_domain_active = allocation_model.search_is_active('=', True, search_time)
        active_allocation = allocation_model.search([('id', 'in', self.allocation_ids.ids)] + search_domain_active)

        if len(active_allocation) > 1:
            raise Exception("Multiple allocation found for the equipment id:{equipment_id}".format(
                equipment_id=self.id))

        allocation_subscription = active_allocation.move_id.subscription_id
        allocation_package = allocation_subscription and allocation_subscription.package_ids or None

        return allocation_package or packages

    @api.multi
    def get_equipment_move(self, search_date_utc=None):
        """Return if it exists, the partner.move at the specified date.

        :param search_date_utc: the date used to search the partner via the assignations (in UTC)
        :return: None or a partner.move (record)
        """
        self.ensure_one()
        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        search_date_time = search_date_utc or self.env.context.get('force_time', datetime.now())
        result = self.env['partner.move']

        if isinstance(search_date_time, (datetime, date)):
            search_date_time = fields.Datetime.to_string(search_date_time)
        elif isinstance(search_date_time, basestring):
            search_date_time = fields.Datetime.to_string(fields.Datetime.from_string(search_date_time))
        else:
            raise ValueError('search_date_utc must be an Odoo date (str) or date object')

        allocation_model = self.env['partner.move.equipment.rel']
        search_active_domain = allocation_model.search_is_active('=', True, search_date=search_date_time)

        allocations = allocation_model.search([('equipment_id', '=', self.id)] + search_active_domain)

        for allocation in allocations:
            if allocation.move_id:
                result += allocation.move_id

        # Trick to remove duplicates
        result = result & result

        return result

    # endregion
    pass
