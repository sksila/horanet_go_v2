from odoo import api, exceptions, fields, models, _


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    partner_category_ids = fields.Many2many(
        string="Partner categories",
        comodel_name='subscription.category.partner'
    )

    date_start = fields.Date(required=True)

    @api.constrains('date_start', 'date_end')
    def _check_end_date_posterior_to_start_date(self):
        """Don't allow `date_end` < `date_start`."""
        for rec in self:
            if not rec.date_end:
                continue

            if rec.date_end <= rec.date_start:
                raise exceptions.ValidationError(_("End date should be posterior to begin date."))
