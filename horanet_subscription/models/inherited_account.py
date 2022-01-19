from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InheritedAccount(models.Model):

    # region Private attributes
    _inherit = 'account.invoice'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    usage_ids = fields.Many2many(
        string="Usages",
        comodel_name='horanet.usage',
        compute='_compute_invoice__usages_ids',
        readonly=True,
        store=True,
    )

    invoice_comment = fields.Char(string="Comment")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def unlink(self):
        """Override methode to unlink usages and update package lines and sale order lines."""
        for rec in self:
            if rec.state not in ['draft']:
                raise ValidationError(_("You can remove a draft invoice only"))

            usages = rec.usage_ids
            # TODO trouver tous les usages qui suivent et les supprimer également ainsi que leurs factures

            # On supprime les usages
            for usage in usages:
                if usage.sale_order_line_id:
                    if usage.is_delivered:
                        if usage.package_line_id.is_salable:
                            # Pour la part variable
                            usage.sale_order_line_id.qty_invoiced = \
                                usage.sale_order_line_id.qty_invoiced - usage.quantity

            usages.mapped('origin_engine_result_id').unlink(engine_force=True)

            # On va chercher les lignes de sale order correspondant aux parts fixes (au cas où pas d'usages)
            origins = rec.origin and [r.strip() for r in rec.origin.split(',')] or []
            sale_orders = self.env['sale.order'].search([('name', 'in', origins)])
            sols = self.env['horanet.package.line'].search(
                [('sale_order_id', 'in', sale_orders.ids)]).mapped('package_order_line_ids')

            sols = sols & rec.invoice_line_ids.mapped('sale_line_ids')

            sols.write({
                'product_uom_qty': 0,
                'qty_delivered': 0,
                'qty_invoiced': 0,
            })

        return super(InheritedAccount, self).unlink()

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.depends('origin', 'invoice_line_ids')
    def _compute_invoice__usages_ids(self):
        """Get the invoiced usages of the sale orders for the corresponding invoice."""
        for rec in self:
            usage_ids = self.env['horanet.usage']
            if rec.origin:
                # On sépare les origines
                origins = rec.origin.split(',')
                for origin in origins:
                    # On va chercher le SO s'il y'en a un
                    so = self.env['sale.order'].search([('name', '=', origin.strip())])
                    if len(so) == 1:
                        # Les usages sont ceux du sale order qui n'ont pas encore de facture
                        usage_ids += so.usage_ids.filtered(lambda r: r.is_delivered and not (r.invoice_ids - rec))

                if usage_ids:
                    # On met le tout dans le champs
                    rec.usage_ids = [(6, 0, usage_ids.ids)]

    # endregion

    pass
