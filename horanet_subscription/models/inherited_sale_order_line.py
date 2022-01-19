from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class SaleOrderLine(models.Model):
    # region Private attributes
    _inherit = 'sale.order.line'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    pricelist_item_id = fields.Many2one('product.pricelist.item')

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
    # flake8: noqa
    @api.multi
    def invoice_create_delivered(self, grouped=False, final=False, manual_debug=True):
        """Create the invoice associated to the sale order lines (SOL).

        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary (invoice negative quantity)
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}

        import logging
        import time
        _logger = logging.getLogger('invoice_create_delivered')
        start_time = time.time()
        _logger.info("Start invoice creation (for {nb_sol} sale.order.lines)".format(nb_sol=str(len(self))))

        filtered_sale_order_lines = self.sorted(
            key=lambda l: float_is_zero(l.qty_delivered - l.qty_invoiced, precision_digits=precision))
        _logger.info(
            "Filter lines without quantity to invoice: {nb_sol} (time: {exec_time:0.3f}s))".format(
                nb_sol=str(len(filtered_sale_order_lines)),
                exec_time=round(time.time() - start_time, 3)))
        nb_sol_invoiced = 0
        # forcer la quantité à se calculer en fonction de la quantité livré, indépendamment du paramétrage de produit
        for sale_order_line in filtered_sale_order_lines:
            nb_sol_invoiced += 1
            if not nb_sol_invoiced % 100:
                _logger.info(
                    "Analyze sol #{sol_number} of {nb_total}".format(
                        sol_number=str(nb_sol_invoiced),
                        nb_total=str(len(filtered_sale_order_lines))))
            sol_order = sale_order_line.order_id
            sol_qty_to_invoice = sale_order_line.qty_delivered - sale_order_line.qty_invoiced
            # ignorer les quantités trop faible pour être facturés
            if float_is_zero(sol_qty_to_invoice, precision_digits=precision):
                continue

            # Création de la clé de regroupement
            if grouped:
                group_key = sol_order.id
            else:
                group_key = (sol_order.partner_invoice_id.id, sol_order.currency_id.id)

            if group_key not in invoices:
                inv_data = sol_order._prepare_invoice()
                invoice = inv_obj.create(inv_data)
                references[invoice] = sol_order
                invoices[group_key] = invoice
            elif group_key in invoices:
                vals = {}
                if sol_order.name not in invoices[group_key].origin.split(', '):
                    vals['origin'] = invoices[group_key].origin + ', ' + sol_order.name
                if sol_order.client_order_ref and sol_order.client_order_ref not in invoices[group_key].name.split(
                        ', ') and sol_order.client_order_ref != invoices[group_key].name:
                    vals['name'] = invoices[group_key].name + ', ' + sol_order.client_order_ref
                invoices[group_key].write(vals)
            if sol_qty_to_invoice > 0:
                sale_order_line.invoice_line_create(invoices[group_key].id, sol_qty_to_invoice)
            elif sol_qty_to_invoice < 0 and final:
                sale_order_line.invoice_line_create(invoices[group_key].id, sol_qty_to_invoice)

        if not invoices:
            if manual_debug:
                raise UserError(_('There is no invoicable line.'))
            else:
                return False

        if references.get(invoices.get(group_key)):
            if sol_order not in references[invoices[group_key]]:
                references[invoice] = references[invoice] | sol_order

        _logger.info("Begin invoice computation ({nb_invoice} invoice created)".format(
            nb_invoice=str(len(list(invoices.values())))
        ))

        nb_invoice = 0
        for invoice in list(invoices.values()):
            nb_invoice += 1
            if not nb_invoice % 100:
                _logger.info("Compute invoice #{invoice_number} of {nb_total}".format(
                    invoice_number=str(nb_invoice),
                    nb_total=str(len(list(invoices.values())))
                ))
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_untaxed < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()

            # A garder ?
            # Helper method to send a mail / post a message using a view_id to
            # render using the ir.qweb engine. This method is stand alone, because
            # there is nothing in template and composer that allows to handle
            # views in batch. This method should probably disappear when templates
            # handle ir ui views.
            # invoice.message_post_with_view('mail.message_origin_link',
            #                                values={'self': invoice, 'origin': references[invoice]},
            #                                subtype_id=self.env.ref('mail.mt_note').id)

        if manual_debug:
            return self.mapped('order_id').action_view_invoice()
        return list(invoices.values())

    # endregion

    pass
