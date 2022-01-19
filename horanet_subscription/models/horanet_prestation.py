from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import exceptions
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from ..tools import date_utils

try:
    from odoo.addons.horanet_go.tools.utils import safe_environment
except ImportError:
    from horanet_go.tools.utils import safe_environment


class HoranetPrestation(models.Model):
    # region Private attributes
    _name = 'horanet.prestation'

    _sql_constraints = [
        ('unique_reference',
         'UNIQUE(reference)',
         "The reference must be unique per prestation"),
    ]

    # endregion

    # region Default methods
    def _default_reference(self):
        return self.env['ir.sequence'].next_by_code('prestation.reference')

    # endregion

    # region Fields declaration
    reference = fields.Char(string="Reference", required=True, copy=False, default=_default_reference)
    name = fields.Char(string="Name", required=True)
    cycle_id = fields.Many2one(
        string="Cycle",
        comodel_name='horanet.subscription.cycle',
        required=True
    )

    device_label = fields.Char(string="Device label")
    description = fields.Text(string="Description")

    impact_fmi = fields.Boolean(string="Impact FMI", default=False)
    need_recipient = fields.Boolean(string="Need recipient", default=False)
    identification_technology_ids = fields.Many2many(string="Identification technologies",
                                                     comodel_name='partner.contact.identification.technology',
                                                     relation='horanet_presation_technology_rel')
    is_blocked = fields.Boolean(string="Is blocked", default=True)
    is_salable = fields.Boolean(string="Is salable")
    balance = fields.Integer(string="Balance")
    service_id = fields.Many2one(
        string="Service",
        comodel_name='horanet.service',
        required=False
    )
    activity_ids = fields.Many2many(
        string="Activities",
        comodel_name='horanet.activity',
        related='service_id.activity_ids',
        readonly=True
    )
    subscription_category_ids = fields.Many2many(
        string="Partner subscription categories",
        comodel_name='subscription.category.partner',
        required=False)
    required_category_domain = fields.Char(
        string="Required subscription categories",
        compute=lambda x: '',
        search='_search_required_category_domain',
        help="Categories needed for a partner to use this prestation. Not for display, just for search",
        store=False)
    use_product = fields.Boolean(string="Set a price")
    product_id = fields.Many2one(string="Product", comodel_name='product.template')
    invoice_type = fields.Selection(string="Invoice type", selection=[('beginning', "Beginning"),
                                                                      ('ending', "Ending")])

    prorata_rule_code = fields.Text(
        string="Prorata code",
        default=(
            "# Place here your code, exemple:\n"
            "# return ratio\n\n"
            "# available parameters are :\n"
            "# theoretical_period (tuple) -> (start_date, end_date)\n"
            "# practical_period (tuple) -> (opening_date, closing_date)\n"
            "# ratio (float) -> ratio of the theoretical/practical periods\n",
            "# Available lib : datetime, relativedelta, date\n"),
        help="Code used to fractionate the balance and the optional fixed price of the package")

    is_derogation = fields.Boolean(
        string="Is derogation",
        compute='_compute_prestation_is_derogation',
        search='_search_prestation_is_derogation',
        store=False,
        help="The property derogation is inherent to the free prestation without balance control and no cycle"
    )

    # endregion

    # region Fields method
    @api.depends('is_salable', 'is_blocked', 'cycle_id')
    def _compute_prestation_is_derogation(self):
        for rec in self:
            is_derogation = False
            if not rec.is_salable and not rec.is_blocked and rec.cycle_id.period_type == 'unlimited':
                is_derogation = True
            rec.is_derogation = is_derogation

        return

    @api.model
    def _search_prestation_is_derogation(self, operator, value):
        if operator not in ['=', '!=']:
            raise NotImplementedError("Got operator '%s' (expected '=' or '!=')" % operator)

        domain = ['&', '&',  # Il est critique de normaliser le domain en explicitant les opérateurs
                  ('is_salable', '=', False),
                  ('is_blocked', '=', False),
                  ('cycle_id.period_type', '=', 'unlimited')]

        # Négation du domaine en cas de recherche négative
        if bool(operator not in expression.NEGATIVE_TERM_OPERATORS) != bool(value):
            domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(domain)

    @api.model
    def _search_required_category_domain(self, operator, value):
        """Recherche des prestations autorisés pour une ou plusieurs catégories, ou un partner (via ses catégories).

        :param operator: Tout les opérateurs, note, les opérateurs de chaîne rechercheront la valeur sur
          le code d'une catégorie
        :param value: une ou plusieurs subscription.category (recordset) ou un id de catégorie, ou une liste d'id
          de catégories ou un res.partner (record), ou une string qui cherchera sur le code d'une catégorie
        :return: Un domaine de recherche de horanet.prestation
        """
        if 'like' in operator and isinstance(value, str):
            value = self.subscription_category_ids.search([('code', operator, value)])
        ids_category = []
        if isinstance(value, models.Model) and value._name == 'res.partner':
            value.ensure_one()
            ids_category = value.subscription_category_ids.ids
        elif isinstance(value, models.Model) and value._name == 'subscription.category.partner':
            ids_category = value.ids
        elif value and isinstance(value, list):
            ids_category = value
        elif value and isinstance(value, (str, int)):
            ids_category = [int(value)]
        domain = ['|',
                  ('subscription_category_ids', '=', False),
                  ('subscription_category_ids', 'in', ids_category)]
        ids_activity = self.activity_ids.search([('required_category_domain', 'not in', ids_category)]).ids
        if ids_activity:
            domain += [('activity_ids', 'not in', ids_activity)]
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [expression.NOT_OPERATOR] + domain

        return expression.normalize_domain(domain)

    # endregion

    # region Constrains and Onchange
    @api.constrains('is_blocked', 'balance')
    def _check_positive_balance(self):
        for r in self.filtered('is_blocked'):
            if r.balance <= 0:
                raise exceptions.ValidationError(_("Balance must be positive"))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_prorata_fraction(self, package_line, start_date, end_date, opening_date, closing_date):
        """Execute the optional python code, computing the prorata ratio, and return the result.

        :param start_date: A string (odoo) representing the start of the theoretical period
        :param end_date: A string (odoo) representing the end of the theoretical period
        :param opening_date: A string (odoo) representing the start of the practical period
        :param closing_date: A string (odoo) representing the end of the practical period
        :return: a ratio (float), or None if no rule or no result
        """
        self.ensure_one()
        if not all([start_date, end_date, opening_date, closing_date]):
            raise ValueError("Missing argument")

        if not self.prorata_rule_code:
            return None

        # wrapper de code afin de rendre disponible l'utilisation du mot clé 'return'
        embedded_prorata_rule_code = "def _embeddedRuleCode_(*args, **kwargs):\n"
        embedded_prorata_rule_code += "\t" + "\n\t".join(self.prorata_rule_code.split('\n'))
        embedded_prorata_rule_code += "\n\tpass\nresult = _embeddedRuleCode_()\n"

        with safe_environment(self.env) as safe_env:
            theoretical_period = (fields.Datetime.from_string(start_date),
                                  date_utils.convert_date_to_closing_datetime(end_date))
            practical_period = (fields.Datetime.from_string(opening_date), fields.Datetime.from_string(closing_date))

            duration_practical = (practical_period[1] - practical_period[0]).total_seconds()
            duration_theoretical = (theoretical_period[1] - theoretical_period[0]).total_seconds()
            ratio = duration_practical / duration_theoretical

            local_context = {
                'result': None,
            }

            global_context = {
                'env': safe_env,
                'package_line': package_line,
                'relativedelta': relativedelta,
                'datetime': datetime,
                'date': date,
                'theoretical_period': theoretical_period,
                'practical_period': practical_period,
                'ratio': ratio,
            }
            # Execution du code python
            safe_eval(embedded_prorata_rule_code,
                      global_context,
                      local_context,
                      mode='exec',
                      nocopy=True)

        result = local_context.get('result', None)
        return result

    # endregion

    pass
