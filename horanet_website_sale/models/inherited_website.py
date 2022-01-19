# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.http import request


class Website(models.Model):
    """Override Website class.

    Override sale_get_order method to delete archived products from cart.
    """

    # region Private attributes
    _inherit = 'website'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def sale_get_order(self, force_create=False, code=None, update_pricelist=False, force_pricelist=False):
        """Override method to delete archived products from cart."""
        sale_order = super(Website, self).sale_get_order(force_create=force_create, code=code,
                                                         update_pricelist=update_pricelist,
                                                         force_pricelist=force_pricelist)

        # Delete archived product from cart only if order is in draft or cancel state
        if sale_order and sale_order.state in ('draft', 'cancel'):
            # Check if order contains order lines before purge
            order_with_lines = True if sale_order.order_line else False

            for order_line in sale_order.order_line:
                if not order_line.product_id.active:
                    order_line.unlink()

            # If no more order line are available in order remove it from session
            if order_with_lines and not sale_order.order_line.exists():
                request.session['sale_order_id'] = None
                return self.env['sale.order']

        return sale_order

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
