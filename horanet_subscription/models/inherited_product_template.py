from odoo import _, api, exceptions, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    nb_pricelist_items = fields.Integer(compute='_compute_nb_pricelist_items', search='_search_nb_pricelist_items')
    pricelist_item_price = fields.Float(compute='_compute_pricelist_item_price')

    @api.depends('item_ids', 'nb_pricelist_items')
    def _compute_pricelist_item_price(self):
        for r in self:
            if r.nb_pricelist_items == 1:
                r.pricelist_item_price = r.item_ids.fixed_price

    @api.depends('item_ids')
    def _compute_nb_pricelist_items(self):
        for r in self:
            r.nb_pricelist_items = len(r.item_ids)

    def _search_nb_pricelist_items(self, operator, value):
        if operator == '=':
            value = False
        elif operator == '!=':
            value = False
        return [('item_ids', operator, value)]

    @api.onchange('item_ids')
    def _onchange_pricelist_items(self):
        """Reset list_price if pricelist items are defined."""
        if self.item_ids:
            self.list_price = 0

    @api.constrains('item_ids')
    def _check_partner_category_and_dates(self):
        """Check if a partner category is in multiple pricelist item."""
        message = _("The category %s is in multiple pricelist with dates that overlap.")

        for rec in self:
            categories_with_dates = {}

            for item in rec.item_ids.sorted('date_start', reverse=True):
                for category in item.partner_category_ids:
                    existing_category = categories_with_dates.get(category.id)

                    if not existing_category:
                        categories_with_dates[category.id] = {'date_start': item.date_start, 'date_end': item.date_end}
                        continue

                    if not existing_category.get('date_end') and not item.date_end:
                        raise exceptions.UserError(message % category.name)

                    elif existing_category.get('date_end') and not item.date_end:
                        if item.date_start <= existing_category.get('date_end'):
                            raise exceptions.UserError(message % category.name)

                    elif not existing_category.get('date_end') and item.date_end:
                        if existing_category.get('date_start') <= item.date_end:
                            raise exceptions.UserError(message % category.name)

                    elif existing_category.get('date_end') and item.date_end:
                        if existing_category.get('date_end') <= item.date_start:
                            raise exceptions.UserError(message % category.name)
