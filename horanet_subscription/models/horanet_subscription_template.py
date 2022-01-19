from odoo import api, fields, models, exceptions, _
from odoo.osv import expression


class ContractTemplate(models.Model):
    # region Private attributes
    _name = 'horanet.subscription.template'
    _inherit = ['application.type']

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    is_renewable = fields.Boolean(string="Is renewable?")
    cycle_id = fields.Many2one(
        string="Cycle",
        comodel_name='horanet.subscription.cycle',
        required=True
    )
    prestation_ids = fields.Many2many(
        string="Prestation config",
        comodel_name='horanet.prestation',
        required=True
    )
    payment_type = fields.Selection(
        string="Payment type",
        selection=[('before', "Before"),
                   ('before_and_after', "Before and after"),
                   ('after', "After")],
    )
    subscription_category_ids = fields.Many2many(
        string="Partner subscription categories",
        comodel_name='subscription.category.partner',
        required=False)
    required_category_domain = fields.Char(
        string="Required subscription categories",
        compute=lambda x: '',
        search='_search_required_category_domain',
        help="Categories needed for a partner to use this template. Not for display, just for search",
        store=False)

    # endregion

    # region Fields method
    @api.model
    def _search_required_category_domain(self, operator, value):
        """Recherche des templates autorisés pour une ou plusieurs catégories, ou un partner (via ses catégories).

        :param operator: Tout les opérateurs. Note: les opérateurs de chaîne rechercheront la valeur sur
          le code d'une catégorie
        :param value: une ou plusieurs subscription.category (recordset) ou un id de catégorie, ou une liste d'id
          de catégories ou un res.partner (record), ou une string qui cherchera sur le code d'une catégorie
        :return: Un domaine de recherche de horanet.subscription.template
        """
        if 'like' in operator and isinstance(value, str):
            value = self.subscription_category_ids.search([('code', operator, value)])
        ids_category = []
        if isinstance(value, models.Model) and value._name == 'res.partner':
            value.ensure_one()
            ids_category = value.subscription_category_ids.ids
        elif isinstance(value, models.Model) and value._name == 'subscription.category.partner':
            ids_category = value.ids
        elif value and isinstance(value, list):
            ids_category = value
        elif value and isinstance(value, (str, int)):
            ids_category = [int(value)]
        domain = ['|',
                  ('subscription_category_ids', '=', False),
                  ('subscription_category_ids', 'in', ids_category)]
        ids_prestation = self.prestation_ids.search([('required_category_domain', 'not in', ids_category)]).ids
        if ids_prestation:
            domain += [('prestation_ids', 'not in', ids_prestation)]
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [expression.NOT_OPERATOR] + domain

        return expression.normalize_domain(domain)

    # endregion

    # region Constrains and Onchange
    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if not rec.name.strip():
                raise exceptions.ValidationError(_("Template name cannot be empty"))

    @api.constrains('prestation_ids')
    def _check_prestation_ids(self):
        """Check if prestations are defined.

        For some reason, the `required=True` is not taken into account when
        creating template programatically.

        :raise: odoo.exceptions.ValidationError if not
        """
        for rec in self:
            if not rec.prestation_ids:
                raise exceptions.ValidationError(
                    _("Please add at least one prestation to the subscription template.")
                )

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
