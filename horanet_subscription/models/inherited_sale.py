from odoo import models, fields, api


class InheritedSale(models.Model):
    """Add some data to sale orders."""

    # region Private attributes
    _inherit = 'sale.order'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    usage_ids = fields.One2many(string="Usages", comodel_name='horanet.usage', inverse_name='sale_order_id',
                                readonly=True)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        We override this method to add the invoice lines to the corresponding usages.

        :return: the id of the new invoice
        """
        ids = super(InheritedSale, self).action_invoice_create(grouped, final)
        for id in ids:
            # On va chercher l'invoice
            invoice = self.env['account.invoice'].browse(id)
            # On va chercher le SO si self, ou les SO si appelé d'une vue liste
            so_ids = self or self.env['sale.order'].browse(self._context.get('active_ids', []))
            for so in so_ids:
                # On va chercher tous les SO lines en rapport avec la facture
                order_lines = so.order_line.filtered(lambda r:
                                                     r.invoice_lines <= invoice.invoice_line_ids
                                                     or r.invoice_lines >= invoice.invoice_line_ids)
                # On va chercher tous les usages en rapport avec ces SO lines
                usages = so.usage_ids.filtered(lambda r:
                                               r.sale_order_line_id.id in order_lines.ids
                                               and not r.is_invoiced)
                for usage in usages:
                    usage.invoice_line_ids += usage.sale_order_line_id.mapped('invoice_lines') \
                        .filtered(lambda r: r.invoice_id == invoice)
                    usage.invoice_ids += usage.sale_order_line_id.mapped('invoice_lines') \
                        .filtered(lambda r: r.invoice_id == invoice) \
                        .mapped('invoice_id')
                # Pour les usages non facturables
                usages2 = so.usage_ids.filtered(lambda r: r.sale_order_id.id == so.id and not r.invoice_ids)
                for usage in usages2:
                    usage.invoice_ids = invoice
        return ids

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
