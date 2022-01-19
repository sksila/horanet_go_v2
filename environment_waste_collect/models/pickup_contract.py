
from odoo import _, api, exceptions, fields, models
from odoo.osv import expression


class PickupContract(models.Model):
    """Class of pickup contracts."""

    # region Private attributes
    _name = 'environment.pickup.contract'

    # endregion

    # region Default methods
    @api.model
    def _default_name(self):
        return self.env['ir.sequence'].next_by_code('seq_environment_pickup_contract')

    # endregion

    # region Fields declaration
    name = fields.Char(string="Reference", default=_default_name)
    activity_ids = fields.Many2many(
        string="Wastes",
        comodel_name='horanet.activity',
        domain="[('application_type', '=', 'environment')]",
        required=True
    )
    service_provider_id = fields.Many2one(
        string="Service provider",
        comodel_name='res.partner',
        domain='[(["is_environment_service_provider", "=", True])]',
        required=True
    )
    begin_date = fields.Date(
        string="Begin date",
        default=fields.Date.context_today,
        required=True
    )
    end_date = fields.Date(string="Ending date")
    is_valid = fields.Boolean(
        string="Is valid",
        compute='_compute_contract_is_valid',
        help="The field is set to true if the contract is not expired",
        search='_search_is_valid',
    )
    waste_site_id = fields.Many2one(
        copy=False,
        string="Waste site",
        comodel_name='environment.waste.site',
        required=True,
    )
    emplacement_ids = fields.Many2many(
        string="Emplacements",
        compute='_compute_emplacement_ids',
        store=False,
        comodel_name='stock.emplacement',
    )
    pickup_delay = fields.Float(string="Pickup delay")
    contract_attachment = fields.Binary(
        string="Contract attachment",
        help="Upload your contract to keep digital copy of the real one")

    environment_pickup_request_ids = fields.Many2many(
        string="Pickup requests",
        comodel_name='environment.pickup.request',
        compute='_compute_contract_environment_pickup_request_ids',
        store=False,
    )
    active_environment_pickup_request_ids = fields.Many2many(
        string="Active pickup requests",
        comodel_name='environment.pickup.request',
        compute='_compute_contract_environment_pickup_request_ids',
        store=False,
    )

    # endregion

    # region Fields method
    @api.depends('activity_ids', 'waste_site_id')
    def _compute_emplacement_ids(self):
        emplacement_model = self.env['stock.emplacement']
        for contract in self:
            contract.emplacement_ids = emplacement_model.search([
                '&',
                ('activity_id', 'in', contract.activity_ids.ids),
                ('waste_site_id', '=', contract.waste_site_id.id)
            ])

    def _compute_contract_environment_pickup_request_ids(self):
        for contract in self:
            pickup_requests = self.env['environment.pickup.request'].search([
                ('contract_id', '=', contract.id)
            ])
            contract.environment_pickup_request_ids = pickup_requests
            contract.active_environment_pickup_request_ids = pickup_requests.filtered(lambda p: p.state == 'progress')

    @api.depends('end_date')
    def _compute_contract_is_valid(self):
        """Compute contract validity."""
        for rec in self:
            if rec.end_date and rec.begin_date <= fields.Date.today() <= rec.end_date:
                rec.is_valid = True
            elif not rec.end_date and rec.begin_date <= fields.Date.today():
                rec.is_valid = True
            else:
                rec.is_valid = False

    @api.multi
    def _search_is_valid(self, operator, value=False):
        u"""Search contracts that are valids.

        :param operator: opérateur de recherche
        :param value: valuer recherché
        :return: Retourne un domain de recherche correspondant à la recherche sur le champ calculé is_valid
        """
        computed_today = fields.Date.today()
        search_domain = [
            '&',
            '|', ('begin_date', '=', False), ('begin_date', '<=', computed_today),
            '|', ('end_date', '=', False), ('end_date', '>=', computed_today)
        ]
        # inversion en cas de recherche négative
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            search_domain = expression.NOT_OPERATOR + search_domain

        return search_domain

    # endregion

    # region Constrains and Onchange
    @api.constrains('begin_date', 'end_date')
    def _check_end_date_posterior_to_begin_date(self):
        """Don't allow `end_date` < `begin_date`."""
        for rec in self:
            if not rec.end_date:
                continue

            if rec.end_date < rec.begin_date:
                raise exceptions.ValidationError(_("End date should be posterior to begin date."))

    @api.multi
    @api.constrains('activity_ids', 'waste_site_id', 'begin_date', 'end_date')
    def _check_unicity(self):
        """Don't allow two contracts on same warehouse and same waste for a given date."""
        # test unicity only in record with waste_site_id and begin_date as these fields are required
        for contract in self.filtered('waste_site_id').filtered('begin_date'):
            search_domain = [
                ('id', '!=', contract.id),
                ('waste_site_id', '=', contract.waste_site_id.id),
                ('activity_ids', 'in', contract.activity_ids.ids),
                '|',
                ('end_date', '=', False),
                ('end_date', '>=', contract.begin_date),
            ]

            if contract.end_date:
                search_domain.extend(['|', ('begin_date', '=', False), ('begin_date', '<=', contract.end_date)])

            duplicate_contract = self.search(search_domain, limit=1)

            if not duplicate_contract:
                continue

            # building the duplicate warning message
            message = _(
                "This contract is not valid."
                "\nAn existing contract: {contract_name} is set with the following conflicting configuration: "
                "\nWaste_site: {waste_site}"
                "\nWaste: {wastes}"
                "\nPeriod: from {begin_period} to {end_period}"
            ).format(
                contract_name=contract.name,
                waste_site=contract.waste_site_id.name,
                wastes="\n\t - ".join((duplicate_contract.activity_ids & contract.activity_ids).mapped('name')),
                begin_period=duplicate_contract.begin_date,
                end_period=duplicate_contract.end_date or _("forever"))

            raise exceptions.ValidationError(message)

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
    pass
