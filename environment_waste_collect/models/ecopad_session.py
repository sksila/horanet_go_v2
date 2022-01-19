
from odoo import fields, models, api, _

ECOPAD_SESSION_STATE = [('open', "Open"), ('closed', "Closed")]


class EcopadSession(models.Model):
    # region Private attributes
    _name = 'environment.ecopad.session'
    _order = 'start_date_time desc'
    _sql_constraints = [
        ('unicity_on_number_and_ecopad', 'UNIQUE(number, ecopad_id)',
         _('The session number must be unique per ecopad'))
    ]
    # endregion

    # region Fields declaration
    # TODO : add computed fields to display session related oparation and query (as for now it's only on operation)
    state = fields.Selection(string="State", selection=ECOPAD_SESSION_STATE, compute='_compute_sate', store=True)

    number = fields.Char(required=True)
    last_number = fields.Char(string="Last number")
    ecopad_id = fields.Many2one(string="Ecopad",
                                comodel_name='horanet.device',
                                required=True,
                                domain="[('is_ecopad', '=', True)]")

    start_date_time = fields.Datetime(string="Start date", default=fields.Datetime.now, required=True)
    end_date_time = fields.Datetime(string="End date")

    tag_id = fields.Many2one(string="Tag id", comodel_name='partner.contact.identification.tag', required=True)
    tag_number = fields.Char(string="Tag number", related='tag_id.number')
    guardian_id = fields.Many2one(string="Guardian", comodel_name='res.partner', required=True)
    waste_site_id = fields.Many2one(string="Waste site", comodel_name='environment.waste.site', required=True)
    activity_sector_ids = fields.Many2many(
        string="Activity sectors",
        comodel_name='activity.sector'
    )
    transaction_ids = fields.One2many(
        string="Transactions",
        comodel_name='environment.ecopad.transaction',
        inverse_name='ecopad_session_id'
    )
    nb_transactions_from_ecopad = fields.Integer(
        string="Number of transactions",
        help="This value is retrieved from Ecopad",
        readonly=True
    )
    wrong_nb_transactions = fields.Boolean(compute='_compute_wrong_nb_transactions')

    is_closing_issue = fields.Boolean(string="Closing issue", compute="_compute_is_closing_issue", store=False)

    operations_ids = fields.Many2many(string="Operations",
                                      compute='_compute_operations_ids',
                                      comodel_name='horanet.operation',
                                      # search="_search_operation_ids",
                                      store=False)
    operations_ids_count = fields.Integer(string="Operations count",
                                          compute='_compute_operations_ids_count',
                                          store=False)
    nb_operations_from_ecopad = fields.Integer(
        string="Number of operations",
        help="This value is retrieved from Ecopad",
        readonly=True
    )
    wrong_nb_operations = fields.Boolean(compute='_compute_wrong_nb_operations')
    # endregion

    # region Fields method
    @api.depends('start_date_time', 'end_date_time')
    def _compute_is_closing_issue(self):
        today = fields.Datetime.from_string(fields.Datetime.now())
        for session in self:
            is_closing_issue = False
            if session.start_date_time and not session.end_date_time:
                if (today - fields.Datetime.from_string(session.start_date_time)).days >= 3:
                    is_closing_issue = True
            session.is_closing_issue = is_closing_issue

    @api.depends('operations_ids')
    def _compute_operations_ids_count(self):
        for session in self:
            session.operations_ids_count = len(session.operations_ids or [])

    @api.depends('transaction_ids.operation_ids')
    def _compute_operations_ids(self):
        for session in self.filtered('transaction_ids'):
            session.operations_ids = session.transaction_ids.mapped('operation_ids')

    @api.depends('end_date_time')
    def _compute_sate(self):
        for session in self:
            session.state = 'closed' if session.end_date_time else 'open'

    @api.depends('transaction_ids', 'nb_transactions_from_ecopad')
    def _compute_wrong_nb_transactions(self):
        """Check if there is an issue for the transactions.

        Compare the number of transactions retrieved from Ecopad and
        the number of transactions available in the database.
        """
        for rec in self:
            if rec.nb_transactions_from_ecopad != len(rec.transaction_ids):
                rec.wrong_nb_transactions = True

    @api.depends('operations_ids', 'nb_operations_from_ecopad')
    def _compute_wrong_nb_operations(self):
        """Check if there is an issue for the operations.

        Compare the number of operations retrieved from Ecopad and
        the number of operations available in the database.
        """
        for rec in self:
            if rec.nb_operations_from_ecopad != len(rec.operations_ids):
                rec.wrong_nb_operations = True
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        res = []
        for session in self:
            name = _(u"{number} {guardian_name} {waste_site_name}".format(
                number=str(session.number),
                guardian_name=str(session.guardian_id.name),
                waste_site_name=str(session.waste_site_id.name)))
            res.append((session.id, name))
        return res

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
