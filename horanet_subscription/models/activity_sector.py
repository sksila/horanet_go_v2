from odoo import models, fields, api, exceptions, _
from odoo.osv import expression


class Activity_sector(models.Model):
    # region Private attributes
    _name = 'activity.sector'
    _rec_name = 'code'
    _sql_constraints = [('unicity_on_code', 'UNIQUE(code)', _("The activity sector code must be unique if not null"))]
    _order = 'parent_id, name'

    # endregion

    # region Default methods
    def default_code(self):
        return self.env['ir.sequence'].next_by_code('activity.sector.code')

    # endregion

    # region Fields declaration
    code = fields.Char(string="Reference", required=True, default=default_code)
    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")

    parent_id = fields.Many2one(string="Parent sector", comodel_name='activity.sector', index=True)
    child_ids = fields.One2many(string="Descendant sector", comodel_name='activity.sector', inverse_name='parent_id')

    use_parent_activity = fields.Boolean(
        string="Use parent activities", default=False)
    custom_activity_ids = fields.Many2many(
        string="Custom activities",
        comodel_name='horanet.activity')
    parent_activity_ids = fields.Many2many(
        string="parent activities",
        comodel_name='horanet.activity',
        related='parent_id.activity_ids',
        readonly=True)
    activity_ids = fields.Many2many(
        string="Activities",
        comodel_name='horanet.activity',
        compute='_compute_activity_ids',
        store=False,
        search='_search_activity_ids')

    is_counting = fields.Boolean(string="Is counting", default=False)
    anti_passback = fields.Boolean(string="Anti passback", default=False)
    anti_passbadge = fields.Boolean(string="Anti passbadge", default=False)

    # endregion

    # region Fields method
    @api.depends('use_parent_activity', 'custom_activity_ids', 'parent_id', 'parent_id.activity_ids')
    def _compute_activity_ids(self):
        for sector in self:
            if sector.use_parent_activity and sector.parent_id:
                sector.activity_ids = sector.parent_id.activity_ids
            else:
                sector.activity_ids = sector.custom_activity_ids

    @api.model
    def _search_activity_ids(self, operator, value=False):
        """
        Override search method for activities.

        :param operator: opérateur de recherche
        :param value: valuer recherché
        :return: Retourne un domain de recherche correspondant à la recherche sur le champ calculé activity_ids
        """
        parent_sector = self.search(['&',
                                     '|', ('use_parent_activity', '=', False), ('parent_id', '=', False),
                                     ('custom_activity_ids', operator, value)])
        result = parent_sector.ids

        while parent_sector:
            enfant_sector = self.search([('use_parent_activity', '=', True),
                                         ('parent_id', 'in', parent_sector.ids)])
            result = result + enfant_sector.ids
            parent_sector = enfant_sector

        search_domain = [('id', 'in', result)]
        # inversion en cas de recherche négative
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            search_domain = expression.NOT_OPERATOR + search_domain

        return search_domain

    # endregion

    # region Constrains and Onchange
    @api.onchange('parent_id')
    def onchange_parent_id(self):
        self.ensure_one()
        if not self.parent_id:
            self.use_parent_activity = False
        elif not self.custom_activity_ids:
            self.use_parent_activity = True

    @api.constrains('parent_id', 'use_parent_activity')
    def check_parent_activity(self):
        for rec in self:
            if rec.use_parent_activity and not rec.parent_id:
                raise exceptions.ValidationError(
                    _("The sector must have a parent in order to use it's activities"))

    @api.constrains('parent_id', 'use_parent_activity', 'custom_activity_ids')
    def check_activity_ids(self):
        for rec in self:
            if rec.parent_id and not rec.custom_activity_ids and not rec.use_parent_activity:
                raise exceptions.ValidationError(
                    _("The sector use parent activities if no custom activities are set"))

    @api.constrains('parent_id')
    def check_parent_id(self):
        for rec in self:
            if rec.parent_id and rec.id and rec.parent_id.id == rec.id:
                raise exceptions.ValidationError(
                    _("A sector cannot be it's own parent"))

    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        """Name_get() -> [(id, name), ...].

        Returns a textual representation for the records in ``self``.
        By default this is the value of the ``display_name`` field.

        :return: list of pairs ``(id, text_repr)`` for each records
        :rtype: list(tuple)
        """
        result = []
        for rec in self:
            result.append((rec.id, str(rec.name) + " (" + str(rec.code) + ")"))
        return result

    # endregion

    # region Actions
    @api.multi
    def action_show_diagram(self):
        """Open the custom diagram view of sector activities and rule activities."""
        self.ensure_one()
        diagram = self.env['wizard.activity.diagram'].create({})
        result = diagram.get_diagram_action_value()
        result.update({'name': _("Sector Diagram")})
        return result

    # endregion

    # region Model methods
    # endregion

    pass
