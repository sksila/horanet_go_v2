from odoo import models, fields, api, exceptions, _
from odoo.osv import expression


class HoranetActivity(models.Model):
    # region Private attributes
    _name = 'horanet.activity'
    _inherit = ['application.type']
    _sql_constraints = [
        ('unicity_on_reference', 'UNIQUE(reference)',
         _('The reference should be unique per activity'))
    ]

    # endregion

    # region Default methods
    def _default_reference(self):
        return self.env['ir.sequence'].next_by_code('activity.reference')

    # endregion

    # region Fields declaration
    active = fields.Boolean(string="Active", default=True)
    reference = fields.Char(string="Reference", required=True, copy=False, default=_default_reference)
    name = fields.Char(string="Name", required=True)

    device_label = fields.Char(string="Device label")
    description = fields.Text(string="Description")

    default_action_id = fields.Many2one(string="Default action", comodel_name='horanet.action', required=True)

    # changing_room_time = fields.Integer(string="Changing room duration")
    product_uom_id = fields.Many2one(string="Unit", comodel_name='product.uom', required=True)
    product_uom_categ_id = fields.Many2one(string="Unit category", comodel_name='product.uom.categ',
                                           compute='_compute_product_uom_categ_id',
                                           store=True)
    default_usage = fields.Integer(string="Default usage")
    product_id = fields.Many2one(string="Product", comodel_name='product.product')

    service_ids = fields.Many2many(string="Services", comodel_name='horanet.service',
                                   relation='horanet_service_activity_rel',
                                   column1='activity_id',
                                   column2='service_id', readonly=True)

    image = fields.Binary(string="Image")

    subscription_category_ids = fields.Many2many(
        string="Partner subscription categories",
        comodel_name='subscription.category.partner',
        required=False)
    required_category_domain = fields.Char(
        string="Required subscription categories",
        compute=lambda x: '',
        search='_search_required_category_domain',
        help="Categories needed for a partner to use this activity. Not for display, just for search",
        store=False)

    # endregion

    # region Fields method
    @api.model
    def _search_required_category_domain(self, operator, value):
        """Recherche des activités autorisés pour une ou plusieurs catégories, ou un partner (via ses catégories).

        :param operator: Tout les opérateurs, note, les opérateurs de chaîne rechercheront la valeur sur
          le code d'une catégorie
        :param value: une ou plusieurs subscription.category (recordset) ou un id de catégorie, ou une liste d'id
          de catégories ou un res.partner (record), ou une string qui cherchera sur le code d'une catégorie
        :return: Un domaine de recherche de horanet.activity
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
        domain = expression.OR([
            [('subscription_category_ids', '=', False)],
            [('subscription_category_ids', 'in', ids_category)]])
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [expression.NOT_OPERATOR] + domain

        return expression.normalize_domain(domain)

    # endregion

    # region Constrains and Onchange
    @api.multi
    @api.constrains('product_id', 'product_uom_id')
    def _check_unit_category(self):
        """Check if the unit defined has the same category has the product unit.

        :raise: odoo.exceptions.ValidationError if not
        """
        for activity in [act for act in self if act.product_id and act.product_uom_id]:
            if activity.product_uom_id.category_id != activity.product_id.uom_id.category_id:
                raise exceptions.ValidationError(
                    _("The unit category must be the same between the product and the activity"))

    @api.multi
    @api.constrains('product_uom_id', 'product_uom_categ_id', 'service_ids')
    def _check_prestation_unit(self):
        for activity in self.filtered(lambda act: act.product_uom_categ_id and act.service_ids):
            for service in activity.service_ids:
                if service.product_uom_categ_id and service.product_uom_categ_id != activity.product_uom_categ_id:
                    raise exceptions.ValidationError(
                        _(("The activity {activity_name} and the prestation "
                           "{presta_name} must have the same unit category")).format(activity_name=activity.name,
                                                                                     presta_name=service.name))

    @api.multi
    @api.depends('product_uom_id')
    def _compute_product_uom_categ_id(self):
        for activity in self:
            activity.product_uom_categ_id = activity.product_uom_id.search(
                [('uom_type', '=', 'reference'),
                 ('category_id', '=', activity.product_uom_id.category_id.id)],
                limit=1).category_id.id

    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = rec.name + ' (' + rec.reference + ')'
            res.append((rec.id, name))
        return res

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
