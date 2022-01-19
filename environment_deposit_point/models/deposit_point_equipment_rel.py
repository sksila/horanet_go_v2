# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions, _


class ProductionPointAttribution(models.Model):
    # region Private attributes
    _name = 'deposit.point.equipment.rel'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    deposit_point_id = fields.Many2one(string="Deposit point", comodel_name='environment.deposit.point', required=True)
    maintenance_equipment_id = fields.Many2one(string="Container", comodel_name='maintenance.equipment', required=True)
    beginning_date = fields.Datetime(string="Beginning date", required=True, default=fields.Datetime.now)
    ending_date = fields.Datetime(sring="Ending date")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('deposit_point_id', 'maintenance_equipment_id', 'beginning_date', 'ending_date')
    def check_unicity(self):
        model = self.env['deposit.point.equipment.rel']
        for rec in self:
            if not rec.beginning_date:
                return

            # Un bac ne peut être en relation qu'avec un seul PAV à un instant t
            relations = model.search([
                ('maintenance_equipment_id', '=', rec.maintenance_equipment_id.id),
                ('id', '!=', rec.id)
            ])

            for relation in relations:
                if (not rec.ending_date and rec.beginning_date <= relation.beginning_date) or \
                 (rec.ending_date and rec.beginning_date <= relation.beginning_date <= rec.ending_date) or \
                 (not relation.ending_date and relation.beginning_date <= rec.beginning_date) or \
                 (relation.ending_date and relation.beginning_date <= rec.beginning_date <= relation.ending_date):
                    raise exceptions.ValidationError(
                        _(u"This equipment is already attributed to another deposit point ({})"
                          .format(relation.deposit_point_id.name)))

            # Un PAV ne peut avoir qu'un seul bac à un instant t
            relations = model.search([
                ('deposit_point_id', '=', rec.deposit_point_id.id),
                ('id', '!=', rec.id)
            ])

            for relation in relations:
                if (not rec.ending_date and rec.beginning_date <= relation.beginning_date) or \
                 (rec.ending_date and rec.beginning_date <= relation.beginning_date <= rec.ending_date) or \
                 (not relation.ending_date and relation.beginning_date <= rec.beginning_date) or \
                 (relation.ending_date and relation.beginning_date <= rec.beginning_date <= relation.ending_date):
                    raise exceptions.ValidationError(
                        _(u"There is already a container at this deposit point for the provided dates"))

    @api.constrains('beginning_date', 'ending_date')
    def check_date_values(self):
        """
        Check the consistency of date values.

        :return: nothing
        :raise: Validation error if beginning date not set or if beginning date superior to ending date
        """
        for rec in self:
            # KO si la date de fin est renseignée mais inférieure à la date de début
            if rec.ending_date and rec.beginning_date > rec.ending_date:
                raise exceptions.ValidationError(_(u"Beginning date must be inferior to ending date"))
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
    pass
