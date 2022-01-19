from odoo import api, fields, models, _, exceptions
from odoo import api, fields, models
from odoo.osv import expression


class Partner(models.Model):
    """Extend res.partner to add medium fields and method about those fields."""

    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    assignation_ids = fields.One2many(
        string="Assignations",
        comodel_name='partner.contact.identification.assignation',
        inverse_name='partner_id',
    )
    active_assignation_count = fields.Integer(
        string="Assignations Count",
        compute='_compute_active_assignation_count',
        search='_search_active_assignation_count',
        store=False,
    )
    tag_ids = fields.Many2many(
        string="Tags",
        comodel_name='partner.contact.identification.tag',
        compute='_compute_tags',
        inverse='_set_tags',
        domain="[('is_assigned', '=', False)]",
        search='_search_partner_tags',
    )
    medium_ids = fields.Many2many(
        string="Mediums",
        comodel_name='partner.contact.identification.medium',
        compute='_compute_mediums',
    )
    has_active_medium = fields.Boolean(
        string="Has active medium",
        compute='_compute_has_active_medium',
        search='_search_has_active_medium'
    )

    # endregion

    # region Fields method

    @api.depends('assignation_ids')
    def _compute_active_assignation_count(self):
        for rec in self:
            rec.active_assignation_count = len(rec.assignation_ids.filtered('is_active'))

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
        SELECT partner_full.id, nb_assignation
        FROM
        ( SELECT partner.id, coalesce(nb_active_assignation, 0) AS nb_assignation
            FROM
            ( SELECT partner.id, coalesce(count(assignation), 0) AS nb_active_assignation
                    FROM res_partner AS partner
                    LEFT OUTER JOIN partner_contact_identification_assignation AS assignation
                        ON partner.id = assignation.partner_id
                    WHERE assignation.start_date <= {percent}
                        AND (assignation.end_date IS NULL
                        OR assignation.end_date > {percent})
                    GROUP BY partner.id
            ) AS partner_assignation
            FULL OUTER JOIN res_partner AS partner ON partner.id = partner_assignation.id
        ) AS partner_full
        WHERE nb_assignation {operator} {percent}
        """.format(operator=operator, percent='%s')

        where_clause_params = [fields.Datetime.now(), fields.Datetime.now(), value]
        self.env.cr.execute(query, where_clause_params)

        ids = map(lambda x: x[0], self.env.cr.fetchall())

        return [('id', 'in', ids)]

    @api.depends()
    def _compute_tags(self):
        """Compute mediums of a partner."""
        for rec in self:
            rec.tag_ids = rec.assignation_ids.filtered('is_active').mapped('tag_id')

    def _set_tags(self):
        """Create assignation for each new tag added."""
        assignation_model = self.env['partner.contact.identification.assignation']

        for rec in self:
            if not rec.tag_ids:
                continue

            for tag in rec.tag_ids:
                assignation_model.create({
                    'tag_id': tag.id,
                    'partner_id': rec.id
                })

    def _search_partner_tags(self, operator, value):
        """Search partner by tags."""
        search_domain = expression.FALSE_DOMAIN
        partner_tags = []
        active_tags = None

        if isinstance(value, bool):
            # Partner has a active tag or not (= has a active assignation or not)
            search_domain = [('assignation_ids.is_active', '!=', False)]

            if bool(operator in expression.NEGATIVE_TERM_OPERATORS) == bool(value):
                search_domain = expression.OR([
                    [('assignation_ids', '=', False)],
                    [('assignation_ids.is_active', '=', False)]
                ])

            return expression.normalize_domain(search_domain)

        elif isinstance(value, str):
            # Partner has a tag with the number = value (value is a basestring)
            active_tags_domain = [
                ('active', '=', True),
                ('number', '=ilike', value)
            ]
            active_tags = self.env['partner.contact.identification.tag'].search(active_tags_domain)

        elif isinstance(value, int):
            # Partner has a active tag with the id = value (value is a int)
            active_tags = self.env['partner.contact.identification.tag'].browse(value)

        if not active_tags:
            return search_domain

        if len(active_tags) == 1:
            partner_tags.append(active_tags.get_tag_partner().id)
        else:
            # If multiple tags with the same number are found (because they are different mapping)
            partner_tags = [tag.get_tag_partner().id for tag in active_tags]

        search_domain = [('id', 'in', partner_tags)]

        if bool(operator in expression.NEGATIVE_TERM_OPERATORS) == bool(value):
            search_domain = [expression.NOT_OPERATOR] + search_domain

        return expression.normalize_domain(search_domain)

    @api.multi
    @api.depends()
    def _compute_mediums(self):
        """Compute mediums of a partner."""
        for rec in self:
            rec.medium_ids = rec.tag_ids.mapped('medium_id')

    @api.depends()
    def _compute_has_active_medium(self):
        """Check if the partner has at least one active medium."""
        for rec in self:
            rec.has_active_medium = rec.medium_ids.filtered('active')

        active_assignation_domain = [
            ('partner_id', 'in', self.ids),
            ('start_date', '>', fields.Datetime.now()),
            '|', ('end_date', '=', False), ('end_date', '<', fields.Datetime.now()),
            ('tag_id.medium_id', '!=', False)
        ]

        active_assignations = self.env['partner.contact.identification.assignation'].search(active_assignation_domain)

        for partner in self:
            if active_assignations.filtered(lambda a: a.partner_id == partner.id):
                partner.has_active_medium = True
            else:
                partner.has_active_medium = False

    def _search_has_active_medium(self, operator, value):
        domain = [
            '&', '&',
            ('assignation_ids.start_date', '<', fields.Datetime.now()),
            '|', ('assignation_ids.end_date', '=', False), ('assignation_ids.end_date', '>=', fields.Datetime.now()),
            ('assignation_ids.tag_id.medium_id', '!=', False)
        ]
        return domain

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
