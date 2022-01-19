
from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError
from odoo.osv import expression


class Partner(models.Model):
    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    is_duplicated = fields.Boolean(string="Is duplicated")
    text_duplicated = fields.Char(
        string="a duplicate",
        compute='_compute_text_duplicated',
        groups='partner_merge.group_contact_merge',
    )
    duplication_count = fields.Integer(
        string="To merge",
        compute='_compute_duplication_count',
        groups='partner_merge.group_contact_merge',
    )

    is_a_duplicate_partner = fields.Selection(
        string='Is potentially a duplicate partner',
        selection=[('no_duplicate', "Not a duplicate partner"),
                   ('same_name', "Same name only"),
                   ('duplicate_partner', "Same name and same birthdate")],
        compute='_compute_is_a_duplicate_partner',
        search='_search_is_a_duplicate_partner',
        default='no_duplicate',
        store=False,
    )

    partner_name_button = fields.Char(
        string="Partner name for button",
        related='name',
        readonly=True,
    )

    not_a_duplicate = fields.Boolean(
        string="Not a duplicate partner",
        default=False,
    )

    # endregion

    # region Fields method
    @api.depends('name', 'birthdate_date')
    def _compute_is_a_duplicate_partner(self):
        """Define if a partner is potentially a duplicate (same name and same birthdate)."""
        # Vérification du droit d'accès à la date de naissance avant de calculer l'âge. Normalement les champs
        # display_age et birthdate_date sont liée par le même groupe, mais des exceptions peuvent survenir.
        can_use_birthdate_date = True
        try:
            self.check_field_access_rights('read', ['birthdate_date'])
        except exceptions.AccessError:
            can_use_birthdate_date = False
        for rec in self:
            domain_same_name = [('name', '=', rec.name)]
            search_partner_same_name = []
            search_not_self = [('id', '!=', rec.id)] if isinstance(rec.id, int) else []
            search_partner_same_name += domain_same_name + search_not_self

            partners_same_name = rec.search(search_partner_same_name)

            if can_use_birthdate_date:
                duplicate_partners = rec.search(
                    search_partner_same_name + ([('birthdate_date', '=', rec.birthdate_date)]))
            else:
                duplicate_partners = False

            if duplicate_partners:
                rec.is_a_duplicate_partner = 'duplicate_partner'

            elif partners_same_name:
                rec.is_a_duplicate_partner = 'same_name'

            else:
                rec.is_a_duplicate_partner = 'no_duplicate'

    @api.multi
    @api.depends('is_duplicated')
    def _compute_text_duplicated(self):
        """Trick to allow us to set a text instead of integer in statsinfo widget."""
        for rec in self:
            rec.text_duplicated = _("Is") if rec.is_duplicated else _("Is not")

    @api.multi
    @api.depends('is_duplicated')
    def _compute_duplication_count(self):
        """Compute the number of duplicated partner."""
        for rec in self:
            rec.duplication_count = rec.search_count([('is_duplicated', '=', 'True')])

    def _search_is_a_duplicate_partner(self, operator, value):
        """Search duplicate partner.

        We use the same method to find duplicate (query) that the odoo merge wizard
        (base.partner.merge.automatic.wizard) for same name and same birthdate.
        """
        search_domain = []

        if value == 'duplicate_partner':
            query = 'SELECT min(id), array_agg(id) FROM res_partner WHERE name IS NOT NULL GROUP BY birthdate_date, ' \
                    'lower(name) HAVING COUNT(*) >= 2 ORDER BY min(id)'

        else:
            query = 'SELECT min(id), array_agg(id) FROM res_partner WHERE name IS NOT NULL GROUP BY ' \
                    'lower(name) HAVING COUNT(*) >= 2 ORDER BY min(id)'

        self._cr.execute(query)

        counter = 0
        for min_id, aggr_ids in self._cr.fetchall():
            # To ensure that the used partners are accessible by the user
            partners = self.env['res.partner'].search([('id', 'in', aggr_ids)])
            if len(partners) < 2:
                continue

            counter += 1
            search_domain = expression.OR([[('id', 'in', partners.ids)], search_domain])

        if value == 'no_duplicate':
            search_domain = [expression.NOT_OPERATOR] + search_domain

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            search_domain = [expression.NOT_OPERATOR] + search_domain
        return search_domain

    # endregion

    # region Constrains and Onchange
    @api.onchange('name', 'birthdate_date')
    def _onchange_is_duplicate_partner(self):
        """Show if a partner is a duplicate."""
        domain_same_name = [('name', '=', self.name)]
        domain_same_birthdate = [('birthdate_date', '=', self.birthdate_date)]

        search_partner_same_name = []
        search_partner_same_name_and_birthdate = []
        search_not_self = [('id', '!=', self.id)] if isinstance(self.id, int) else []
        search_partner_same_name += domain_same_name + search_not_self
        search_partner_same_name_and_birthdate += domain_same_name + domain_same_birthdate + search_not_self

        partners_same_name = self.search(search_partner_same_name)
        duplicate_partners = self.search(search_partner_same_name_and_birthdate)

        if duplicate_partners or partners_same_name:
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _("Warning is potentially a duplicate partner ({explanation}).").format(
                        explanation=_("same name and same birthdate") if duplicate_partners else _("same name"))}
            }

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_wizard_duplication(self):
        """Launch the wizard used to merge partners."""
        self.ensure_one()

        duplicated_partner = self.search([('is_duplicated', '=', 'True')]).ids

        if len(duplicated_partner) < 2:
            raise UserError(
                _("There must be at least 2 records flagged as "
                  "duplicate for the merge to work"))

        context = self.env.context.copy()
        context['active_ids'] = duplicated_partner

        wizard = self.env.ref('crm.base_partner_merge_automatic_wizard_form')

        return {
            'name': "Deduplicate Contacts",
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': wizard.id,
            'res_model': 'base.partner.merge.automatic.wizard',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
            'domain': '[]',
        }

    @api.multi
    def action_display_duplicate_partner(self):
        """Show partners who have the same name."""
        self.ensure_one()

        return {
            'name': "Duplicate Partners",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('partner_merge.res_partner_duplicate_tree_view').id, 'tree'),
                (self.env.ref('partner_contact_citizen.view_citizen_form').id, 'form')
            ],
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('name', '=', self.name)]
        }

    @api.multi
    def action_toggle_is_duplicate(self):
        """Set the inverse value of is_duplicated field."""
        for rec in self:
            if rec.is_duplicated and rec.not_a_duplicate is False:
                rec.not_a_duplicate = True
            elif not rec.is_duplicated and rec.not_a_duplicate is True:
                rec.not_a_duplicate = False
            rec.is_duplicated = not rec.is_duplicated

    # endregion

    # region Model methods
    # endregion
