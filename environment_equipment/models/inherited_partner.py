# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.osv import expression


class ResPartner(models.Model):
    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration

    equipment_allocations_ids = fields.Many2many(
        string="Environment containers",
        comodel_name='partner.move.equipment.rel',
        compute='_compute_equipment_allocations_ids',
        store=False
    )
    active_equipment_allocations_ids = fields.Many2many(
        string="Active environment containers",
        comodel_name='partner.move.equipment.rel',
        compute='_compute_active_equipment_allocations_ids_and_count',
        store=False,
    )
    active_equipment_allocations_count = fields.Integer(
        string="Active environment containers count",
        compute='_compute_active_equipment_allocations_ids_and_count',
        search='_search_active_equipment_allocations_count',
        store=False,
    )

    # endregion

    # region Fields method
    @api.depends('partner_move_ids')
    def _compute_equipment_allocations_ids(self):
        """Recherche les allocations des partners, actif ou inactifs."""
        allocation_model = self.env['partner.move.equipment.rel']
        for rec in self:
            if rec.id:
                rec.equipment_allocations_ids = allocation_model.search([('move_id', 'in', rec.partner_move_ids.ids)])

    @api.depends('partner_move_ids')
    def _compute_active_equipment_allocations_ids_and_count(self):
        """Recherche les allocations des partner, actif ou inactifs."""
        if not self.ids:
            return
        query = """
            SELECT partner.id,
                   coalesce(nb_equipment, 0) AS nb_equipment,
                   allocation_ids
            FROM
              (SELECT partner.id,
                      count(alloc) AS nb_equipment,
                      array_agg(alloc.id) AS allocation_ids
               FROM res_partner AS partner
               LEFT OUTER JOIN partner_move AS MOVE ON partner.id = move.partner_id
               LEFT OUTER JOIN partner_move_equipment_rel AS alloc ON alloc.move_id = move.id
               WHERE partner.id IN ({sql_partner_ids})
                 AND move.start_date <= {percent}
                 AND (move.end_date IS NULL
                      OR move.end_date > {percent})
                 AND alloc.start_date <= {percent}
                 AND (alloc.end_date IS NULL
                      OR alloc.end_date > {percent})
               GROUP BY partner.id
               HAVING COUNT(alloc) >= 1) AS partner_with_equipment
            FULL OUTER JOIN res_partner AS partner ON partner.id = partner_with_equipment.id
            WHERE partner.id IN ({sql_partner_ids}) AND nb_equipment >=1
        """.format(percent='%s', sql_partner_ids=','.join([str(partner_id) for partner_id in self.ids]))

        where_clause_params = [fields.Datetime.now() for i in range(4)]
        self.env.cr.execute(query, where_clause_params)

        equipment_by_partner_id = dict(map(lambda x: (x[0], x[1:]), self.env.cr.fetchall()))
        # dict(self.env.cr.fetchall())

        partner_without_equipment = self.filtered(lambda p: p.id not in equipment_by_partner_id.keys())
        partner_without_equipment.write({
            'active_equipment_allocations_ids': None,
            'active_equipment_allocations_count': 0
        })
        for partner in self - partner_without_equipment:
            partner.active_equipment_allocations_count = equipment_by_partner_id[partner.id][0]
            partner.active_equipment_allocations_ids = equipment_by_partner_id[partner.id][1]

    def _search_active_equipment_allocations_count(self, operator, value):
        if operator not in ['=', '!=', '<=', '<', '>', '>=']:
            raise exceptions.UserError(_("Operator ({bad_operator}) not supported".format(bad_operator=operator)))

        # Raise exception if value is not an int or a string representing an integer
        if type(value) is bool:
            if value == bool(operator not in expression.NEGATIVE_TERM_OPERATORS):
                return [(1, '=', 1)]
            else:
                return ['!', (1, '=', 1)]

        value = int(value)

        query = """
            SELECT partner_full.id
            FROM
            (SELECT partner.id,
                       coalesce(nb_alloc, 0) AS nb_equip
                FROM
                  (SELECT partner.id,
                          count(alloc) AS nb_alloc
                   FROM res_partner AS partner
                   LEFT OUTER JOIN partner_move AS MOVE ON partner.id = move.partner_id
                   LEFT OUTER JOIN partner_move_equipment_rel AS alloc ON alloc.move_id = move.id
                   WHERE move.start_date <= {percent}
                     AND (move.end_date IS NULL
                          OR move.end_date > {percent})
                     AND alloc.start_date <= {percent}
                     AND (alloc.end_date IS NULL
                          OR alloc.end_date > {percent})
                   GROUP BY partner.id) AS partner_with_equipment
                FULL OUTER JOIN res_partner AS partner ON partner.id = partner_with_equipment.id) AS partner_full
            WHERE nb_equip {operator} {percent}
        """.format(operator=operator, percent='%s')

        where_clause_params = [fields.Datetime.now() for i in range(4)] + [value]
        self.env.cr.execute(query, where_clause_params)

        ids = map(lambda x: x[0], self.env.cr.fetchall())

        return [('id', 'in', ids)]

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
