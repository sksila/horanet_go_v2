from odoo import models, fields, api, exceptions, _
from odoo.osv import expression


class HoranetContractLineDetail(models.Model):
    # region Private attributes
    _name = 'horanet.package.line.detail'
    _rec_name = "display_name"
    _sql_constraints = [
        ('unicity', 'UNIQUE(package_line_id,activity_id)', _('The line must be unique by activity/contract'))]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    display_name = fields.Char(string='Name', compute='_get_display_name',
                               store=False, readonly=True)
    package_line_id = fields.Many2one(string="Contract line", comodel_name='horanet.package.line',
                                      required=True, readonly=True)
    subscription_id = fields.Many2one(related='package_line_id.subscription_id')
    activity_id = fields.Many2one(string="Activity", comodel_name='horanet.activity',
                                  readonly=True)
    product_id = fields.Many2one(string="Product", comodel_name='product.product', related='activity_id.product_id',
                                 readonly=True)
    usage_quantity = fields.Float(string="Usage quantity", compute='compute_usage_quantity',
                                  store=True, readonly=True)
    usage_line_ids = fields.Many2many(string="Usages lines", comodel_name='horanet.usage',
                                      compute='compute_usage_line_ids', search='search_usage_line_ids',
                                      store=False)
    sale_order_id = fields.Many2one(related='package_line_id.sale_order_id', comodel_name='sale.order',
                                    store=False, readonly=True)
    sale_order_line_id = fields.Many2one(string="Sale order line", comodel_name='sale.order.line',
                                         readonly=True)

    # endregion

    # region Fields method
    @api.multi
    @api.depends('package_line_id', 'product_id')
    def _get_display_name(self):
        for line in self:
            line.display_name = str(line.subscription_id and line.subscription_id.name or '') + str(
                line.product_id and line.product_id.display_name or '')

    @api.multi
    @api.depends('package_line_id.usage_ids', 'product_id')
    def compute_usage_line_ids(self):
        for line in self:
            line.usage_line_ids = line.package_line_id.usage_ids.filtered(
                lambda u: u.activity_id.product_id == line.product_id)

    def search_usage_line_ids(self, operator, value):
        """Search the usages for a package line detail."""
        if not isinstance(value, list):
            value = [value]
        domain = [('id', 'in', value)]
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [expression.NOT_OPERATOR] + domain

        usages = self.env['horanet.usage'].search(domain)
        return [('id', 'in', usages.ids)]

    @api.multi
    @api.depends('usage_line_ids.quantity')
    def compute_usage_quantity(self):
        for line in self:
            line.usage_quantity = sum([u.quantity for u in line.usage_line_ids])

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def unlink(self):
        for line in self.filtered(lambda line: line.sale_order_line_id):
            raise exceptions.UserError(_('Cannot delete a line bound to a sale order line.'))
        return super(HoranetContractLineDetail, self).unlink()

    # endregion

    # region Actions
    @api.multi
    def action_compute_package_line(self):
        self.ensure_one()
        if not self.sale_order_line_id and self.sale_order_id:
            self.sale_order_line_id = self._get_or_create_sale_order_line()
        self.sale_order_line_id.product_uom_qty = self.usage_quantity
        self.sale_order_line_id.qty_delivered = self.usage_quantity

    def _action_create_order_line(self, order_id=False):
        order_line_model = self.env['sale.order.line']

        inv_line = {
            'order_id': order_id.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.usage_quantity,
            'name': 'custom ' + self.product_id.display_name,
        }
        # Oldlin trick
        order_line = order_line_model.sudo().create(inv_line)

        # inv_line.update(price_unit=line.price_unit, discount=line.discount)
        return order_line

    # endregion

    # region Model methods
    @api.multi
    def _get_or_create_sale_order_line(self):
        self.ensure_one()
        if self.sale_order_line_id:
            return self.sale_order_line_id
        else:
            return self._action_create_order_line(order_id=self.sale_order_id)

    # endregion

    pass
