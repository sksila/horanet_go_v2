from odoo import models, fields, api
from ..tools import date_utils

try:
    from odoo.addons.mail.models.mail_template import format_date
except ImportError:
    from mail.models.mail_template import format_date


class HoranetSubscriptionLine(models.Model):
    """Class classe."""

    # region Private attributes
    _name = 'horanet.subscription.line'
    _inherit = ['horanet.subscription.shared']

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    subscription_id = fields.Many2one(
        string="Subscription",
        comodel_name='horanet.subscription',
        ondelete='cascade',
        required=True,
        index=True,
        oldname='contract_id')

    sale_order_id = fields.Many2one(string="Sale order", comodel_name='sale.order')

    # region dates
    start_date = fields.Date(
        string="Cycle start date",
        oldname='starting_date',
        readonly=True,
        required=True)
    end_date = fields.Date(
        string="Cycle end date",
        oldname='ending_date',
        readonly=True)
    opening_date = fields.Datetime(
        string="Opening date",
        help="Date at which the subscription line is active",
        required=True)
    closing_date = fields.Datetime(
        string="Closing date",
        help="Date at which the subscription line is inactive")

    # Defined in horanet.subscription.shared
    display_opening_date = fields.Char(help="Date at which the subscription line is active")
    display_closing_date = fields.Char(help="Date at which the subscription line is inactive")
    state = fields.Selection(help="Subscription line state")

    # endregion
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    def get_so_name_subscription_line(self, package_line, usage=False):
        """
        Compute the sale order name according to a subscription line.

        :param package_line: the package name for the name
        :param usage: optional usage for the product
        :return: name of the sale order
        """
        start_date = format_date(self.env, self.start_date)
        end_date = format_date(self.env, self.end_date)
        if usage:
            name = "%s: %s (%s - %s)" % (package_line.name, usage.activity_id.product_id.name,
                                         start_date, end_date)
        else:
            name = "%s: %s (%s - %s)" % (package_line.name, package_line.product_id.name,
                                         start_date, end_date)
        return name

    def get_subscription_line(self, usage=False, package_line=False):
        """
        Get the subscription line corresponding to an usage.

        :param usage: the usage
        :return: subscription line corresponding to the usage
        """
        subscription_line = False
        if usage:
            search_date = fields.Datetime.from_string(usage.usage_date).date()
            subscription_line = self.search([
                ('start_date', '<=', search_date),
                ('end_date', '>=', search_date),
                ('id', 'in', usage.package_line_id.subscription_id.line_ids.ids)
            ])
        if package_line:
            subscription_line = self.search([
                ('start_date', '<=', package_line.start_date),
                ('end_date', '>=', package_line.end_date),
                ('id', 'in', package_line.subscription_id.line_ids.ids)
            ])

        return subscription_line

    def get_or_create_sale_order(self):
        """Get or create the sale order for an invoice cycle.

        :return: the sale order
        """
        self.ensure_one()

        if not self.sale_order_id:
            self.sale_order_id = self.env['sale.order'].create({
                'partner_id': self.subscription_id.client_id.id,
                'partner_invoice_id': self.subscription_id.client_id.id,
                'partner_shipping_id': self.subscription_id.client_id.id,
                'validity_date': self.subscription_id.end_date
            })
            self.sale_order_id.action_confirm()
        else:
            self.sale_order_id.action_confirm()

        return self.sale_order_id

    @api.multi
    def get_or_create_sale_order_line(self, usage, name):
        """Create the sale order lines for an usage.

        :param usage: the usage
        :param name: name of the sale order line
        """
        self.ensure_one()

        if not usage and not name:
            return

        price = 0.0
        pricelist_item = usage.get_pricelist_item(self.sale_order_id.partner_id)
        if pricelist_item:
            price = pricelist_item.fixed_price
        else:
            price = usage.activity_id.product_id.list_price

        # Les activités n'ayant pas toutes la même unité, on remet la quantité dans l'unité de référence
        quantity = 0.0
        activity_unit = usage.activity_id.product_uom_id
        product_unit = usage.activity_id.product_id.uom_id

        if activity_unit != product_unit:
            # Si il y a un facteur multiplicateur, alors on divise la quantité par ce facteur.
            # Par ex si l'activité en en L alors que l'unité de référence est en m3, alors on
            # divise la quantité par 1000 pour ramener en m3
            if activity_unit.factor:
                quantity = usage.quantity / activity_unit.factor
            elif activity_unit.factor_inv:
                quantity = usage.quantity * activity_unit.factor_inv
            else:
                quantity = usage.quantity
        else:
            quantity = usage.quantity

        sale_order_line_model = self.env['sale.order.line']
        order_line = sale_order_line_model.search([
            ('order_id', '=', self.sale_order_id.id),
            ('product_id', '=', usage.activity_id.product_id.id),
            ('pricelist_item_id', '=', pricelist_item.id),
            ('name', '=', name)
        ])

        if order_line:
            order_line.product_uom_qty += quantity

        else:
            order_line = self.env['sale.order.line'].create({
                'order_id': self.sale_order_id.id,
                'product_id': usage.activity_id.product_id.id,
                'price_unit': price,
                'pricelist_item_id': pricelist_item.id,
                'product_uom_qty': quantity,
                'product_uom': usage.activity_id.product_id.uom_id.id,
                'name': name,
            })

        return order_line

    @api.model
    def create_subscription_line(self, opening_date, subscription):
        sale_order_id = self.env['sale.order'].create({
            'partner_id': subscription.client_id.id,
            'partner_invoice_id': subscription.client_id.id,
            'partner_shipping_id': subscription.client_id.id,
            'validity_date': subscription.cycle_id.get_end_date_of_cycle(opening_date)
        })
        closing_date = subscription.cycle_id.get_end_date_of_cycle(opening_date)
        closing_date = date_utils.convert_date_to_closing_datetime(closing_date)

        return self.create({
            'start_date': subscription.cycle_id.get_start_date_of_cycle(opening_date),
            'end_date': subscription.cycle_id.get_end_date_of_cycle(opening_date),
            'opening_date': opening_date,
            'closing_date': closing_date,
            'subscription_id': subscription.id,
            'sale_order_id': sale_order_id.id
        })

    # endregion

    pass
