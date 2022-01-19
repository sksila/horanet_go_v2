import logging

import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, tools, _
from odoo.osv import expression
from ..tools import date_utils

try:
    from odoo.addons.mail.models.mail_template import format_date
except ImportError:
    from mail.models.mail_template import format_date

_logger = logging.getLogger(__name__)


class HoranetPackageLine(models.Model):
    # region Private attributes
    _name = 'horanet.package.line'
    _inherit = ['horanet.subscription.shared']
    _rec_order = 'starting_date desc'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)

    # dates
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
        help="Date at which the package line is active",
        required=True)
    closing_date = fields.Datetime(
        string="Closing date",
        help="Date at which the package line is inactive")

    # Defined in horanet.subscription.shared
    display_opening_date = fields.Char(help="Date at which the package line is active")
    display_closing_date = fields.Char(help="Date at which the package line is inactive")
    state = fields.Selection(help="Package line state")
    # endregion

    recipient_id = fields.Many2one(string="Recipient", comodel_name='res.partner')
    subscription_id = fields.Many2one(string="Contract", comodel_name='horanet.subscription')
    package_id = fields.Many2one(
        string="Package",
        comodel_name='horanet.package',
        ondelete='cascade',
        index=True,
        required=True)
    sale_order_id = fields.Many2one(string="Sale order", comodel_name='sale.order')
    package_order_line_ids = fields.Many2many(string="Sale order lines", comodel_name='sale.order.line')

    usage_ids = fields.One2many(string="Usage line", comodel_name='horanet.usage', inverse_name='package_line_id',
                                ondelete='set null')

    package_line_detail_ids = fields.One2many(
        string="Package line details",
        comodel_name='horanet.package.line.detail',
        inverse_name='package_line_id'
    )

    prestation_id = fields.Many2one(string="Prestation", comodel_name='horanet.prestation')

    activity_ids = fields.Many2many(string="Activities", comodel_name='horanet.activity',
                                    related='package_id.activity_ids', store=False)

    is_blocked = fields.Boolean(string="Is blocked", default=True)
    is_salable = fields.Boolean(string="Is salable")

    use_product = fields.Boolean(string="Set a price")
    product_id = fields.Many2one(string="Product", comodel_name='product.template')

    balance_initial = fields.Float(string="Initial balance")
    balance_total = fields.Float(string="Total balance", readonly=True, compute='_compute_balance_total', store=True)
    balance_remaining = fields.Float(string="Remaining balance", compute='_compute_remaining_balance')

    package_price_prorata = fields.Float(
        string="Balance prorata",
        default=1,
        digits=dp.get_precision('Product Unit of Measure'),
        help="This is the quantity, by default 1, set when we need to set a fraction of the package line.")

    is_derogation = fields.Boolean(
        string="Is derogation",
        compute='_compute_package_line_is_derogation',
        search='_search_package_line_is_derogation',
        store=False,
        help="The property derogation is inherent to the free packages without balance control and no cycle"
    )

    # endregion

    # region Fields method
    @api.depends('is_salable', 'is_blocked', 'package_id')
    def _compute_package_line_is_derogation(self):
        for rec in self:
            is_derogation = False
            if not rec.is_salable and not rec.is_blocked and rec.package_id.cycle_id.period_type == 'unlimited':
                is_derogation = True
            rec.is_derogation = is_derogation

        return

    @api.model
    def _search_package_line_is_derogation(self, operator, value):
        if operator not in ['=', '!=']:
            raise NotImplementedError("Got operator '%s' (expected '=' or '!=')" % operator)

        domain = ['&', '&',  # Il est critique de normaliser le domain en explicitant les opérateurs
                  ('is_salable', '=', False),
                  ('is_blocked', '=', False),
                  ('package_id.cycle_id.period_type', '=', 'unlimited')]

        # Négation du domaine en cas de recherche négative
        if bool(operator not in expression.NEGATIVE_TERM_OPERATORS) != bool(value):
            domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(domain)

    @api.multi
    @api.depends('prestation_id')
    def get_prestation_category_ids(self):
        for contract in self:
            contract.prestation_category_ids = contract.prestation_id.mapped('subscription_category_ids')

    @api.multi
    @api.depends('balance_total')
    def _compute_remaining_balance(self):
        for contract in self:
            contract.balance_remaining = contract.balance_initial - contract.balance_total

    @api.multi
    @api.depends('usage_ids.quantity')
    def _compute_balance_total(self):
        for contract in self:
            contract.balance_total = sum([u.quantity for u in contract.usage_ids])

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def compute_package_line(self):
        self._update_contract_line_details()

    @api.multi
    def action_recompute_operations(self):
        self.env['wizard.operation.recompute'].with_context(
            {'default_package_line_ids': self}).create({}).action_multi_recompute()
    # endregion

    # region Model methods
    def bill_package_lines(self, package_line_ids=False):
        """
        Bill package lines.

        :param package_line_ids: optional package lines to bill
        :return: sale orders and sale order lines
        """
        # On facture les packages avec des produits (forfait)
        domain = [('use_product', '!=', False), ('product_id', '!=', False)]
        if package_line_ids:
            domain.append(('id', 'in', package_line_ids.ids))
        package_lines = self.search(domain)
        _logger.info("Starting computing " + str(len(package_lines)) + " package lines")

        package_lines._bill_package_lines()

        # On facture les usages qui n'ont pas de sale order si gratuit ou de sale order line si payant
        domain = ['|',
                  '&', ('package_line_id.is_salable', '=', True), ('sale_order_line_id', '=', False),
                  '&', ('package_line_id.is_salable', '=', False), ('sale_order_id', '=', False)]
        if package_line_ids:
            domain.append(('package_line_id', 'in', package_line_ids.ids))

        # On prend tous les usages selon le domaine
        usages = self.env['horanet.usage'].search(domain)
        if usages:
            _logger.info("Starting computing " + str(len(usages)) + " usages")
            usages.bill_usages()

    def _bill_package_lines(self):
        """
        Create the sale orders for package lines.

        :return: a list of sale orders.
        """
        loop = 0
        for line in self:
            # Un log avec progression pour info
            loop += 1
            if loop % 10 == 0:
                progress = round(loop / float(len(self)), 2) * 100
                _logger.info("Computing package lines " + str(progress) + "%")

            # If there is no product on the activity
            if not line.product_id:
                continue

            # If the prorata is zero
            if line.package_price_prorata == 0.0:
                continue

            # On cherche la subscription line correspondante
            subscription_line = self.env['horanet.subscription.line'].get_subscription_line(package_line=line)

            if not subscription_line:
                # In case the invoice cycle isn't created yet, for a usage in the futur
                # for example, we don't need to create the sale order
                continue

            if len(subscription_line) != 1:
                continue

            # Nom unique du sale order line
            so_line_name = subscription_line.get_so_name_subscription_line(line)

            # On va chercher le sale order
            so = subscription_line.get_or_create_sale_order()
            line.sale_order_id = so.id

            # On va créer le sale order line
            line.get_or_create_sale_order_line(so_line_name)

            # Si il y a un prorata
            if line.package_price_prorata < 1.0:
                so_line_name = _("Refund ") + so_line_name
                line.get_or_create_sale_order_line(so_line_name, line.package_price_prorata)

    def get_or_create_sale_order_line(self, name, prorata=0):
        """
        Get or create the sale order line for a package line.

        :param name: name of the sale order line
        :return: the sale order line
        """
        price = 0.0
        partner_categories = self.recipient_id.mapped('subscription_category_ids')
        pricelist_items = self.product_id.mapped('item_ids')

        start_date = format_date(self.env, self.start_date, tools.DEFAULT_SERVER_DATE_FORMAT)

        pricelist_item = pricelist_items \
            .filtered(lambda p: partner_categories & p.partner_category_ids) \
            .filtered(lambda p: p.date_start and p.date_start <= start_date or not p.date_start) \
            .filtered(lambda p: p.date_end and p.date_end >= start_date or not p.date_end)

        if len(pricelist_item) > 1:
            # We return the pricelist item that will be the cheapest
            pricelist_item = pricelist_item.sorted('fixed_price')[0]

        if pricelist_item:
            price = pricelist_item.fixed_price
        else:
            price = self.product_id.list_price

        # Ici la quantité est de 1 par défaut, sinon il dépend du prorata
        prorata_qty = prorata - 1 if prorata else 1
        quantity = 1.0 * prorata_qty

        sale_order_line_model = self.env['sale.order.line']
        sol = sale_order_line_model.search([
            ('order_id', '=', self.sale_order_id.id),
            ('product_id', '=', self.product_id.id),
            ('pricelist_item_id', '=', pricelist_item.id),
            ('name', '=', name)
        ])
        # Si aucun sale order line trouvé on le crée
        if not sol:
            sol = self.env['sale.order.line'].create({
                'order_id': self.sale_order_id.id,
                'product_id': self.product_id.id,
                'price_unit': price,
                'pricelist_item_id': pricelist_item.id,
                'product_uom_qty': quantity,
                'product_uom': self.product_id.uom_id.id,
                'name': name,
            })
            self.package_order_line_ids = [(4, sol.id)]
        else:
            if sol not in self.package_order_line_ids:
                self.package_order_line_ids = [(4, sol.id)]

            # Sinon si on fait un prorata et que celui-ci a changé
            if (prorata or not sol.product_uom_qty) and sol.product_uom_qty != quantity:
                # Alors on met à jour la quantité sur la ligne de prorata
                sol.product_uom_qty = quantity

    def update_sale_order_lines_qty_delivered(self, date_start, date_end):
        """
        Update the quantity delivered for sale order lines.

        :param date_start: date start
        :param date_end: date end
        :return: list of updated sale order lines
        """
        updated_sol_ids = self.env['sale.order.line']
        loop = 0
        # Formatage des dates en datetime string
        date_end = fields.Datetime.to_string(date_utils.convert_date_to_closing_datetime(date_end))
        date_start += " 00:00:00"
        for line in self:
            # Progression
            loop += 1
            if loop % 100 == 0:
                progress = round(loop / float(len(self)), 2) * 100
                _logger.info("Computing package lines " + str(progress) + "%")

            # On prend les usages de la périodes facturables (non traités)
            if line.is_salable:
                usages = line.usage_ids.filtered(lambda r:
                                                 date_end >= r.usage_date >= date_start
                                                 and r.activity_id.product_id and not r.is_delivered)

                # On ne créer le SO que pour les usages qui n'en ont pas pour gagner du temps
                usages_not_billed = usages.filtered(lambda r: not r.sale_order_id)
                if usages_not_billed:
                    usages_not_billed.bill_usages()

                # On prend les sale order lines
                sol_ids = usages.mapped('sale_order_line_id')

                # Pour les lignes déjà mises à jour, on les sélectionne
                already_delivered_sol = line.usage_ids.filtered(lambda r:
                                                                date_end >= r.usage_date >= date_start
                                                                and r.activity_id.product_id and r.is_delivered) \
                    .mapped('sale_order_line_id')

                # On ne lance la mécanique que si on a un package line facturable
                for sol in sol_ids:
                    # On rassemble les usages avec le sale order line actuel
                    usages_with_sol = usages.filtered(lambda r: r.sale_order_line_id == sol)
                    # On ajoute la quantité délivrée sur la ligne
                    # La quantité délivrée est la somme des quantité des usages de cette ligne
                    sol.qty_delivered += sum([u.quantity for u in usages_with_sol])
                    usages_with_sol.write({'is_delivered': True})

                if already_delivered_sol not in sol_ids:
                    updated_sol_ids += already_delivered_sol
                updated_sol_ids += sol_ids
            # Pour les package lines non facturables et forfait
            if not line.is_salable:
                # Pour les usages gratuits, on les flags en "livrés"
                usages = line.usage_ids.filtered(lambda r:
                                                 date_end >= r.usage_date >= date_start
                                                 and not r.is_delivered)
                usages.write({'is_delivered': True})

                # Si la ligne est un forfait
                if line.use_product and line.product_id:
                    line._bill_package_lines()

                    for sol in line.package_order_line_ids:
                        sol.qty_delivered = sol.product_uom_qty

                    updated_sol_ids += line.package_order_line_ids

                # On ne créer le SO que pour les usages qui n'en ont pas pour gagner du temps
                usages_not_billed = usages.filtered(lambda r: not r.sale_order_id)
                if usages_not_billed:
                    usages_not_billed.bill_usages()

        return updated_sol_ids

    @api.multi
    def get_balance(self, activities=False):
        """Retourne la somme des soldes (non bloqué).

        Cette méthode ne tiens pas compte de la date ou l'état de la ligne
        Si activities est valué, seul les forfait contenant l'ensemble des activités sont pris en compte

        :param activities: Optionnel, un ou plusieurs record 'horanet.activity', utilisé pour filtrer les forfaits
        :return int: Le solde cumulé restant
        """
        if activities and not isinstance(activities, models.Model):
            raise ValueError("Bad Argument 'activities' should be a recordset")
        if activities:
            affected_package_lines = self.filtered(lambda l: activities <= l.activity_ids)
        else:
            affected_package_lines = self

        return sum([rec.balance_remaining for rec in affected_package_lines if rec.balance_remaining > 0])

    @api.multi
    def can_use(self, quantity, activities=False):
        """Détermine si le la quantité demandé est inférieur ou égale au solde restant.

        Si activities est valué, seul les forfait contenant l'une des activités sont pris en compte

        :param quantity: La quantité à décompter du solde
        :param activities: Optionnel, un ou plusieurs record 'horanet.activity', utilisé pour filtrer les forfaits
        :return boolean: True si le solde est suffisant, False sinon
        """
        if activities and not isinstance(activities, models.Model):
            raise ValueError("Bad Argument 'activities' should be a recordset")
        # Si aucun forfait n'existe, retourner False car il n'existe pas de droits
        if len(self) == 0:
            return False
        if activities:
            affected_package_lines = self.filtered(lambda l: activities <= l.activity_ids)
        else:
            affected_package_lines = self

        # Si il exist un forfait illimité, le solde est "infini"
        if affected_package_lines.filtered(lambda r: not r.is_blocked):
            result = True
        else:
            result = (quantity <= affected_package_lines.get_balance())
        return result

    @api.multi
    def _update_contract_line_details(self):
        for rec in self:
            for activity in rec.usage_ids.mapped('activity_id'):
                if not rec.package_line_detail_ids.filtered(lambda d: d.activity_id == activity):
                    rec.package_line_detail_ids.create({
                        'activity_id': activity.id,
                        'package_line_id': rec.id
                    })

    @api.model
    def create_package_line(self, opening_date, package):
        balance = package.balance
        start_date = package.cycle_id.get_start_date_of_cycle(opening_date)
        end_date = package.cycle_id.get_end_date_of_cycle(opening_date)

        package_lines = package.line_ids.sorted('start_date')

        # In case the new line won't be a full period line
        # TODO: fuck this is ugly
        for line in package_lines:
            if line.start_date <= end_date and line.start_date > start_date:
                end_date = package.cycle_id.get_previous_day_date(line.start_date)
                break

        closing_date = date_utils.convert_date_to_closing_datetime(end_date)

        return self.create({
            'name': package.name,
            'recipient_id': package.recipient_id.id,
            'subscription_id': package.subscription_id.id,
            'prestation_id': package.prestation_id.id,
            'is_blocked': package.is_blocked,
            'is_salable': package.is_salable,

            'start_date': start_date,
            'end_date': end_date,
            'opening_date': opening_date,
            'closing_date': closing_date,

            'balance_initial': balance,
            'package_id': package.id,
            'use_product': package.use_product,
            'product_id': package.product_id.id,
        })

    # endregion

    pass
