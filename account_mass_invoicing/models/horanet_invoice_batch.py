# -*- coding: utf-8 -*-

import ast
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.addons.website.models.website import slugify
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

STATES_BATCHES = [('to_generate', 'To generate'), ('generated', 'Generated'), ('locked', 'Locked')]


class HoranetInvoiceBatch(models.Model):
    """This model represent batch of invoices.

    It will enable creation of account invoices according to a type and a campaign.
    """

    # region Private attributes
    _name = 'horanet.invoice.batch'
    _sql_constraints = [('unicity_on_type_and_campaign', 'CHECK(1=1)',
                         _("The type cannot be twice on the same campaign"))]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name",
        compute='_compute_name',
        readonly=True,
    )

    state = fields.Selection(
        string="State",
        selection=STATES_BATCHES,
        default='to_generate'
    )

    type_id = fields.Many2one(
        string="Type",
        comodel_name='horanet.invoice.batch.type',
        required=True,
    )
    campaign_id = fields.Many2one(
        string="Campaign",
        comodel_name='horanet.invoice.campaign',
        required=True,
    )
    invoice_ids = fields.One2many(
        string="Invoices",
        comodel_name='account.invoice',
        inverse_name='batch_id',
        readonly=True,
    )
    role_ids = fields.One2many(
        string="Roles",
        comodel_name='horanet.role',
        inverse_name='batch_id',
        readonly=True,
    )

    domain = fields.Char(string="Domain")

    amount_total = fields.Float(
        string='Total', store=True,
        readonly=True, compute='_compute_amount'
    )

    invoice_number = fields.Integer(
        string='Number of invoices',
        store=True,
        readonly=True,
        compute='_compute_invoice_number'
    )

    message_time_recover_valuation = fields.Char(
        string="Indicate the time on which we are allowed to recover the valuation of old usages",
        compute='_compute_time_of_prestation_recovery',
        store=False,
    )

    message_amount_total_rejected = fields.Char(
        string="Indicate the sum of invoices rejected because their amount are inferior to 15 euros",
        readonly=True,
    )

    # endregion

    # region Fields method
    @api.depends('type_id', 'campaign_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "{} - {} - {}".format(rec.id, rec.type_id.name or '', rec.campaign_id.name or '')

    @api.depends('invoice_ids')
    def _compute_amount(self):
        for rec in self:
            rec.amount_total = sum(line.amount_total for line in rec.invoice_ids)

    @api.depends('invoice_ids')
    def _compute_invoice_number(self):
        for rec in self:
            rec.invoice_number = len(rec.invoice_ids)

    @api.depends('campaign_id')
    def _compute_time_of_prestation_recovery(self):
        """Indicate the config of the number of month allowed to recover the valuation of old usages."""
        for rec in self:
            nb_month = self.env['account.config.settings'].get_time_of_prestation_recovery()
            if nb_month == "0":
                message = ""
            else:
                message = _("Warning: if you generate this batch, {nb_month} month(s) are allowed to recover "
                            "the valuation of old usages.").format(nb_month=nb_month, )
            rec.message_time_recover_valuation = message

    # endregion

    # region Constrains and Onchange
    @api.constrains('state')
    def _lock_invoice(self):
        """Lock invoice if state is in locked."""
        if self.state == 'locked':
            invoices = self.invoice_ids
            offset = 0
            limit = 50
            _logger.info("Starting validation of batch's invoices ({nb_total})".format(nb_total=str(len(invoices))))
            while offset < len(invoices):
                invoices_block = invoices[offset:min(offset + limit, len(invoices))]
                offset += limit
                _logger.info("Starting block {current_nb} of {nb_total}".format(
                    current_nb=str(offset - limit) + '-' + str(offset),
                    nb_total=str(len(invoices))
                ))

                invoices_block.action_invoice_open()
            _logger.info("Ending validation of batch's invoices")

    @api.constrains('type_id', 'campaign_id')
    def _check_application_type(self):
        """Check if application type of type_id and campaign_id are the same."""
        for rec in self:
            if rec.campaign_id.budget_code_id.application_type != rec.type_id.application_type:
                raise ValidationError(_("The campaign and the batch must have the same application type"))

    # endregion

    # region CRUD (overrides)
    @api.multi
    def unlink(self):
        """Override method to unlink usages and update package lines and sale order lines."""
        for rec in self:
            rec.invoice_ids.unlink()

        return super(HoranetInvoiceBatch, self).unlink()

    # endregion

    # region Actions
    def action_generate(self):
        self.ensure_one()

        # Initialisations
        result = ''
        _logger = logging.getLogger('%s (%s)' % (self.type_id.name, self.domain))
        _logger.info("Début de génération du lot (%s)" % self.type_id.name)
        ids_invoices = []

        #  Recherche des contrats à facturer
        domain = [
            ('client_id.subscription_category_ids', 'in', [self.type_id.partner_category_id.id]),
            ('application_type', 'in', [self.type_id.application_type]),
        ]
        if self.type_id.payment_mode_id:
            domain = expression.AND([domain, [('payment_mode', '=', self.type_id.payment_mode_id.id)]])

        if self.domain:
            domain = expression.AND([domain, ast.literal_eval(self.domain)])

        subscriptions = self.env['horanet.subscription'].search(domain, order='id')
        result += _("Nombre de contrats à facturer : %d") % len(subscriptions) + '\n'
        _logger.info("Nombre de contrats à facturer : %d" % len(subscriptions))

        # Pour chaque couple prestation/période de la campagne
        offset = 0
        limit = 500
        time_of_prestation_recovery = self.env['account.config.settings'].get_time_of_prestation_recovery()

        while offset < len(subscriptions):
            subscriptions_block = subscriptions.search(domain, limit=limit, offset=offset, order='id')
            offset += limit
            _logger.info("Starting block {current_nb} of {nb_total}".format(
                current_nb=str(offset - limit) + '-' + str(offset),
                nb_total=str(len(subscriptions))
            ))

            sale_order_lines_to_invoice_block = self.env['sale.order.line']

            # Sale order lines to invoice depending on prestations
            for prestation_period in self.campaign_id.prestation_period_ids:
                # Mise à jour / création des lignes d'encours de facturation
                for prestation_id in prestation_period.prestation_ids:
                    _logger.info("Starting prestation %s" % prestation_id.name)

                    # on définit la date de début de la prestation en incluant une durée sur laquelle on s'autorise
                    # à récupérer des valorisation d'anciens usages non facturés (par défaut = 0)
                    prestation_start_date = fields.Date.to_string(
                        (fields.Date.from_string(prestation_period.start_date) -
                         relativedelta(months=int(time_of_prestation_recovery))
                         )
                    )

                    sale_order_lines_to_invoice_block += subscriptions_block.prepare_sale_order_lines_qty_delivered(
                        prestation_id, prestation_start_date, prestation_period.end_date)

            # Sale order lines to invoice depending on products
            if self.campaign_id.product_ids:
                partners_block = subscriptions_block.mapped('client_id')
                sale_order_lines_product_to_invoice = self.env['sale.order.line'].search([
                    ('invoice_status', '=', 'to invoice'),
                    ('product_id', 'in', self.campaign_id.product_ids.ids),
                    ('order_partner_id', 'in', partners_block.ids),
                ])
                for sol in sale_order_lines_product_to_invoice:
                    sol.write({'qty_delivered': sol.product_uom_qty})

                sale_order_lines_to_invoice_block += sale_order_lines_product_to_invoice

            # Création des factures
            if sale_order_lines_to_invoice_block:
                invoice_block = sale_order_lines_to_invoice_block.invoice_create_delivered(final=True,
                                                                                           manual_debug=False)
                if invoice_block:
                    ids_invoices += invoice_block

        # Mise à jour des factures avec le lot
        #   !! invoices est une liste d'ids
        invoices = self.env['account.invoice'].browse([inv.id for inv in ids_invoices])
        invoices.write({
            'batch_id': self.id,
        })

        # On ne peut pas émettre de factures en dessous du seuil de 15E
        all_invoices_inf = self.env['account.invoice'].search_read([
            ('id', 'in', invoices.ids),
            ('amount_total_signed', '>=', 0.00),
            ('amount_total_signed', '<=', 15.00)
        ], ['amount_total_signed'])

        total_invoices_inf = sum(inv['amount_total_signed'] for inv in all_invoices_inf)

        # on supprime les factures de - 15E afin de pouvoir re-facturer les usages
        self.env['account.invoice'].browse([inv['id'] for inv in all_invoices_inf]).unlink()

        # on avertie l'utilisateur du total non facturé
        message = _("The sum total of invoices rejected because they are inferior or equal to 15 euros is {total} "
                    "({nb_invoices} invoices). {nb_month} month(s) were used to recover the valuation of old usages."
                    ).format(total=total_invoices_inf,
                             nb_invoices=len(all_invoices_inf),
                             nb_month=time_of_prestation_recovery,
                             )

        self.message_amount_total_rejected = message

        result += _("Nombre de factures créées : {nb_invoice_created}").format(
            nb_invoice_created=str((len(ids_invoices or []) - len(all_invoices_inf or []))) + '\n'
        )

        self.state = 'generated'
        _logger.info("Fin de génération du lot ({lot_name})".format(lot_name=self.type_id.name))

        return result

        # TODO gestion des exceptions !!

    # endregion

    # region Model methods
    @api.multi
    def action_merge(self):
        if len(self) < 2:
            raise ValidationError(_("You must select at least two batches to merge them"))

        #  Si pas même type ou pas même campagne
        if len(self.mapped('type_id')) > 1 or len(self.mapped('campaign_id')) > 1:
            raise ValidationError(_("Batches with different type or campaign cannot be merged"))

        # Si déjà dans un rôle
        if self.mapped('role_ids'):
            raise ValidationError(_("Batches already in a role cannot be merged"))

        # Si pas généré
        states = set(self.mapped('state'))
        if len(states) != 1 or 'generated' not in states:
            raise ValidationError(_("Batches that are not in state 'generated' cannot be merged."))

        # Cumul des factures à modifier
        invoices = self.env['account.invoice']
        for rec in self[1:]:
            invoices += rec.invoice_ids

        # On met toutes les factures sur le premier lot
        invoices.write({'batch_id': self[0].id})

        # On supprime tous les autres lots
        self[1:].unlink()

    def slugify_batch_report_name(self):
        """This method make the report file name as a valid URL.

        :return: The string of the file name (ex: 18-environment-particulier.pdf)
        """
        slugify_name = slugify(self.name) + ".pdf"

        return slugify_name

    # endregion

    pass
