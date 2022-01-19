# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.osv import expression


class EnvironmentProductionResPartner(models.Model):
    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    partner_move_ids = fields.One2many(
        string="Moves",
        comodel_name='partner.move',
        inverse_name='partner_id',
        readonly=True
    )
    move_assignation_ids = fields.One2many(
        string="Moves related assignations",
        comodel_name='partner.contact.identification.assignation',
        compute='_compute_move_assignation_ids',
        store=False,
    )

    # endregion

    # region Fields method
    @api.depends('partner_move_ids')
    def _compute_move_assignation_ids(self):
        u"""Recherche des assignations liée aux emménagements du partner (partner -> move -> assignations."""
        for partner in self:
            partner.move_assignation_ids = partner.partner_move_ids.mapped('assignation_ids')

    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    @api.depends('assignation_ids', 'move_assignation_ids')
    def _compute_active_assignation_count(self):
        u"""Surchage 'provisoire' de la méthode de recherche du nombre d'assignation.

        Attention, le champ active_assignation_count n'est pas liée au champ active_assignation

        -  active_assignation -> assignations liée au partenaire
        -  active_assignation_count -> assignations du partenaire + assignation des emménagements du partenaire
        """
        active_moves = self.env['partner.move'].search([
            ('partner_id', 'in', self.ids or []), ('is_active', '=', True)])
        active_moves_assignations = self.env['partner.contact.identification.assignation'].search([
            ('move_id', 'in', active_moves.ids or []), ('is_active', '=', True)])

        for rec in self:
            rec.active_assignation_count = \
                len(rec.assignation_ids.filtered('is_active')) + \
                len(active_moves_assignations.filtered(lambda a: a.move_id in rec.partner_move_ids))

    def _search_active_assignation_count(self, operator, value):
        if operator not in ['=', '!=', '<=', '<', '>', '>=']:
            raise exceptions.UserError(_("Operator ({bad_operator}) not supported".format(bad_operator=operator)))

        if type(value) is bool:
            if value == bool(operator not in expression.NEGATIVE_TERM_OPERATORS):
                return [(1, '=', 1)]
            else:
                return ['!', (1, '=', 1)]
        # Raise exception if value is not an int or a string representing an integer
        value = int(value)

        query = """
        SELECT id, nb_assignation_total FROM (
            SELECT id, coalesce(nb_assignation, 0) AS nb_assignation_total
            FROM
            (   SELECT partner_id, coalesce(count(active_assignation_id), 0) AS nb_assignation
                FROM
                (   SELECT partner.id AS partner_id, assignation.id AS active_assignation_id
                    FROM res_partner AS partner
                    LEFT OUTER JOIN partner_contact_identification_assignation AS assignation
                        ON partner.id = assignation.partner_id
                    WHERE assignation.start_date <= {percent}
                        AND (assignation.end_date IS NULL OR assignation.end_date > {percent})

                    UNION ALL

                    SELECT partner.id AS partner_id, move_assignation.id AS active_assignation_id
                    FROM res_partner AS partner
                    LEFT OUTER JOIN partner_move AS MOVE ON partner.id = move.partner_id
                    LEFT OUTER JOIN partner_contact_identification_assignation AS move_assignation
                        ON move.id = move_assignation.move_id
                    WHERE move.start_date <= {percent}
                        AND (move.end_date IS NULL OR move.end_date > {percent})
                        AND move_assignation.start_date <= {percent}
                        AND (move_assignation.end_date IS NULL
                            OR move_assignation.end_date > {percent})
                ) AS partner_active_assignation
                GROUP BY partner_id
            ) AS partner_assignation
            FULL OUTER JOIN res_partner AS partner ON partner.id = partner_assignation.partner_id
        ) AS partner_global
        WHERE nb_assignation_total {operator} {percent}
        """.format(operator=operator, percent='%s')

        where_clause_params = [fields.Datetime.now() for i in range(6)] + [value]
        self.env.cr.execute(query, where_clause_params)

        ids = map(lambda x: x[0], self.env.cr.fetchall())

        return [('id', 'in', ids)]
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
