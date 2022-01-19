# coding: utf-8

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime, date


class EquipmentAllocation(models.Model):
    u"""Modèle de liaison entre les bacs ('maintenance.equipment') et les emménagements ('partner.move')."""

    # region Private attributes
    _name = 'partner.move.equipment.rel'
    _rec_name = 'equipment_id'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    equipment_id = fields.Many2one(
        string="Equipment",
        comodel_name='maintenance.equipment',
        required=True,
        index=True)
    move_id = fields.Many2one(
        string="Move",
        comodel_name='partner.move',
        required=True,
        index=True)

    start_date = fields.Datetime(required=True, default=fields.Datetime.now)
    end_date = fields.Datetime()
    is_active = fields.Boolean(compute='_compute_is_active', search='search_is_active')

    chip_number = fields.Char(related='equipment_id.chip_number', readonly=True)
    tub_number = fields.Char(related='equipment_id.tub_number', readonly=True)
    category_id = fields.Many2one(related='equipment_id.category_id')

    is_move_id_active = fields.Boolean(related='move_id.is_active')

    # endregion

    # region Fields method
    @api.depends('start_date', 'end_date')
    def _compute_is_active(self):
        """Compute the active property of the allocation at the current date."""
        search_date = fields.Datetime.now()

        for allocation in self:
            if allocation.end_date:
                allocation.is_active = allocation.start_date <= search_date < allocation.end_date
            else:
                allocation.is_active = allocation.start_date <= search_date

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
            ('end_date', '=', False), ('end_date', '>', search_date_time)
        ]

        if (value and operator == '!=') or (not value and operator == '='):
            domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(domain)

    # endregion

    # region Constrains and Onchange
    @api.constrains('start_date', 'end_date')
    def _check_date_consistency(self):
        for rec in self:
            if not rec.end_date:
                continue

            if rec.end_date < rec.start_date:
                raise ValidationError(_("End date should be posterior or equal to start date."))

    @api.constrains('equipment_id', 'move_id', 'start_date', 'end_date')
    def _check_unicity(self):
        u"""Ajout d'une contrainte de vérification de duplicité d'allocation.

        Permet d'éviter d'avoir deux allocations de bac sur la même période
        """
        for allocation in self:
            duplicity_domain = [
                ('id', '!=', allocation.id),
                ('equipment_id', '=', allocation.equipment_id.id)]

            duplicity_domain.extend([
                ('start_date', '>=', allocation.start_date),
                '|',
                ('end_date', '=', False),
                ('end_date', '>', allocation.start_date)
            ])

            if allocation.end_date:
                duplicity_domain.extend([
                    '|',
                    ('start_date', '<=', allocation.end_date),
                    '|',
                    ('end_date', '=', False),
                    ('end_date', '<', allocation.end_date)
                ])

            duplicates = self.search(duplicity_domain)

            # Si doublon's) trouvés retourner une exception ORM
            if duplicates:
                raise ValidationError(_(
                    "Duplicate allocation ({duplicate_ids}) found for the equipment id {equip_id}"
                    " for the period {periode}.".format(
                        duplicate_ids=str(','.join([str(dup_id) for dup_id in duplicates.ids])),
                        equip_id=str(allocation.equipment_id.id),
                        periode="{start_date} <--> {end_date}".format(
                            start_date=str(allocation.start_date),
                            end_date=str(allocation.end_date) if allocation.end_date else '...'
                        )
                    )
                ))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
