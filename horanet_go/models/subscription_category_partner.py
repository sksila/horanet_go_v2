from odoo import models, fields, api, exceptions, _
import ast

FORBIDDEN_FIELDS = ['company_id']


class PartnerCategory(models.Model):
    # region Private attributes
    _name = 'subscription.category.partner'
    _inherit = ['application.type']
    _sql_constraints = [
        ('unicity_on_code', 'UNIQUE(code)', _('The code must be unique')),
        ('unicity_on_domain_and_app_type', 'UNIQUE(domain, application_type)',
         _('The domain must be unique per application type'))
    ]

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", translate=True, required=True)
    domain = fields.Char(string="Domain", required=True)
    code = fields.Char(string="Code", required=True, copy=False)

    partner_ids = fields.Many2many(string="partner",
                                   comodel_name='res.partner',
                                   compute='_get_partner_ids',
                                   search='_search_partner_ids',
                                   store=False, )
    color = fields.Integer(string="Color Index")
    # endregion

    # region Fields method
    @api.depends('domain')
    def _get_partner_ids(self):
        for cate in self:
            if cate.domain:
                cate.partner_ids = self.env['res.partner'].search(ast.literal_eval(cate.domain))
            else:
                cate.partner_ids = None

    @api.model
    def _search_partner_ids(self, operator, value):
        """
        Search method to search partners in this category domain.

        :return: a domain
        """
        ids = []

        # Convert int to list to be able to find intersection
        if isinstance(value, int):
            value = [value]

        for cate in self.search([]):
            if set(value) & set(cate.partner_ids.ids):
                ids.append(cate.id)

        return [('id', 'in', ids)]

    # endregion

    # region Constrains and Onchange
    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if not rec.name.strip():
                raise exceptions.ValidationError(_('Name cannot be empty.'))

    @api.constrains('domain')
    def _check_domain(self):
        for cate in self:
            try:
                ast.literal_eval(self.domain or '[]')

                if not self.env.context.get('domain_fixed'):
                    cate.fix_domain_and_get_context()
            except (ValueError, SyntaxError):
                raise exceptions.ValidationError(_("Unvalid domain expression : malformed string"))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_domain(self):
        self.ensure_one()
        return ast.literal_eval(self.domain or '[]')

    @api.multi
    def fix_domain_and_get_context(self):
        self.ensure_one()

        fixed_domain = []
        context = {}
        partner_model = self.env['res.partner']

        domain = ast.literal_eval(self.domain)
        # Check for any non list element in the domain
        if any(not isinstance(criteria, (list, tuple)) and criteria != '&' for criteria in domain):
            return context

        for criteria in domain:
            if criteria == '&':
                continue

            field_name, operator, value = criteria[0], criteria[1], criteria[2]
            context_value = value

            if operator not in ['=', '!='] or isinstance(partner_model._fields[field_name], fields.One2many):
                fixed_domain.append([field_name, operator, value])
                continue

            if isinstance(partner_model._fields[field_name], fields.Many2one):
                if not isinstance(value, int):
                    record = self.env[partner_model[field_name]._name].search([('name', '=', value)])
                    value = record.id if record else int(value)

                context_value = value

            elif isinstance(partner_model._fields[field_name], fields.Many2many):
                if value is not False:
                    if not isinstance(value, int):
                        record = self.env[partner_model[field_name]._name].search([('name', '=', value)])
                        if record:
                            value = record.id
                        if value.isnumeric():
                            value = int(value)

                    # Special command for Many2many fields
                    context_value = [(4, value)]

            if operator == '=' and field_name not in FORBIDDEN_FIELDS:
                context['default_' + field_name] = context_value

            fixed_domain.append([field_name, operator, value])

        if self.domain != fixed_domain:
            self.with_context(domain_fixed=True).domain = fixed_domain

        return context
    # endregion

    pass
