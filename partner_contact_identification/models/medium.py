from odoo import api, exceptions, fields, models, _
from odoo.osv import expression


class Medium(models.Model):
    """A medium carry one or more tags and allow a citizen to use some services."""

    # region Private attributes
    _name = 'partner.contact.identification.medium'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    type_id = fields.Many2one(
        string="Type",
        comodel_name='partner.contact.identification.medium.type',
        required=True
    )
    tag_ids = fields.One2many(
        string="Tag list",
        comodel_name='partner.contact.identification.tag',
        inverse_name='medium_id'
    )
    partner_id = fields.Many2one(
        string="Holder",
        comodel_name='res.partner',
        compute='_compute_partner_id',
        search='_search_partner_id'
    )
    active = fields.Boolean(string="Active", default=True)
    deactivated_by = fields.Many2one(string="Deactivated by", comodel_name='res.users')
    deactivated_on = fields.Datetime(string="Deactivated on")
    is_lost = fields.Boolean("Lost")

    # endregion

    # region Fields method

    @api.depends('tag_ids.partner_id')
    def _compute_partner_id(self):
        """Set the partner of the medium's tags on the medium."""
        for rec in self.filtered('tag_ids'):
            try:
                rec.partner_id = rec.tag_ids.mapped('partner_id')
            except ValueError:
                raise exceptions.ValidationError(
                    _("Anomaly detected: multiple partners found for tags of the medium %s") % rec.id
                )

    def _search_partner_id(self, operator, value):
        """
        Search partners.

        :param operator: search operator
        :param value: searched value
        :return: a domain that filters on the id or name field
        """
        if not isinstance(value, int) and not isinstance(value, list):
            raise exceptions.UserError(
                _("Search partner on mediums: Expected integer or list of integer, found %s") % value
            )

        if isinstance(value, int):
            value = [value]

        assignation_model = self.env['partner.contact.identification.assignation']
        assignations = assignation_model.search([
            ('partner_id', 'in', value),
            ('end_date', '=', False)
        ])

        domain = [('id', 'in', assignations.mapped('tag_id.medium_id').ids)]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain.insert(0, expression.NOT_OPERATOR)

        return domain

    # endregion

    # region Constrains and Onchange
    @api.constrains('tag_ids')
    def _check_tags_are_assigned_to_same_record(self):
        """Tags set on the medium should be assigned to same record."""
        assignation_model = self.env['partner.contact.identification.assignation']
        for rec in self:
            assignations = assignation_model.search([
                ('tag_id', 'in', rec.tag_ids.ids),
                ('end_date', '=', False)
            ])

            if len(assignations.mapped('reference_id')) > 1:
                raise exceptions.ValidationError(_("Tags on the same medium should be assigned to the same entity."))

    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        """Return the display name of the record."""
        result = []
        for rec in self:
            name = '{} {}'.format(rec.type_id.name, rec.partner_id.name or '')
            result.append((rec.id, name))
        return result

    # endregion

    # region Actions
    @api.multi
    def deallocate(self):
        """Deallocate the medium."""
        related_partner_ids = self.mapped('partner_id')
        if related_partner_ids:
            related_partner_ids.check_access_rule('write')

        assignations = self.env['partner.contact.identification.assignation'].search([
            ('tag_id', 'in', self.mapped('tag_ids').ids),
            ('is_active', '=', True),
        ])
        assignations.end_assignation()

    @api.multi
    def set_lost(self):
        """Deactivate a medium, its tags and their assignations."""
        related_partner_ids = self.mapped('partner_id')
        if related_partner_ids:
            related_partner_ids.check_access_rule('write')

        self.mapped('tag_ids').deactivate()
        self.write({
            'active': True,
            'is_lost': True,
            'deactivated_by': self.env.context.get('uid'),
            'deactivated_on': fields.Datetime.now()
        })

    @api.multi
    def action_open_medium_form(self):
        """Display the form view of medium."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'partner.contact.identification.medium',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.id
        }

    # endregion

    # region Model methods
    @api.model
    def create_medium(self, tag_ids, type_id=False):
        """Create one medium with one or multiple tags.

        :param tag_ids: recordset of tag to attach to the medium
        :param type_id: the record of the medium type
        """
        medium_type = type_id or self.env['partner.contact.identification.medium.type'].search([], limit=1)

        medium_rec = self.with_context(active_test=False).search([('tag_ids', 'in', tag_ids.ids)])

        if not medium_rec:
            return self.create({
                'tag_ids': [(6, 0, tag_ids.ids)],
                'type_id': medium_type.id
            })
        else:
            medium_rec.active = True
            medium_rec.tag_ids = [(6, 0, tag_ids.ids)]
            medium_rec.tag_ids.write({'active': True})
    # endregion

    pass
