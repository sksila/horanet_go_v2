from dateutil.relativedelta import relativedelta

from openerp import _, api, fields, models
from openerp.exceptions import ValidationError


class PartnerRelationFoyer(models.Model):
    """Represents a relation between multiple partners inside the same foyer."""

    # region Private attributes
    _name = 'horanet.relation.foyer'
    _sql_constraints = [
        ('unicity_on_relation', 'UNIQUE(foyer_id,partner_id)',
         _('The relation between a partner and a foyer must be unique'))
    ]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    foyer_id = fields.Many2one(
        string='Foyer',
        comodel_name='res.partner',
        required=True,
        ondelete='restrict',
        domain="[('company_type','=','foyer')]",
        delegate=False)
    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True,
        ondelete='restrict',
        domain="[('company_type','=','person')]",
        delegate=False)
    begin_date = fields.Date(string='Begin date', default=fields.Date.context_today)
    end_date = fields.Date(string='End date')
    is_valid = fields.Boolean(
        string='Is valid',
        compute='_compute_is_valid',
        store=False,
        search='_search_is_valid')
    is_responsible = fields.Boolean(string='Is responsible', copy=False)
    foyer_active_partners = fields.One2many(
        string='Current members',
        comodel_name='res.partner', store=False,
        related='foyer_id.active_foyer_member_ids')
    computed_list_name_foyer_members = fields.Char(
        string='List foyer members name',
        compute='_compute_list_name',
        store=False)

    # endregion

    # region Fields method
    @api.depends('foyer_active_partners')
    def _compute_list_name(self):
        """Compute members' names of a family."""
        for rec in self:
            name = ''
            if rec.foyer_active_partners and len(rec.foyer_active_partners) > 0:
                list_name = []
                for partner in rec.foyer_active_partners:
                    list_name.append(partner.display_name)
                name = u', '.join(list_name)
            rec.computed_list_name_foyer_members = name

    @api.depends('begin_date', 'end_date')
    def _compute_is_valid(self):
        """Compute the validity of a relation."""
        for rec in self:
            is_valid = True
            if rec.begin_date and rec.begin_date > fields.Date.today():
                is_valid = False
            elif rec.end_date and rec.end_date < fields.Date.today():
                is_valid = False
            rec.is_valid = is_valid

    def _search_is_valid(self, operator, value):
        u"""Recherche des relation valides à la date du jour.

        :param operator: opérateur de recherche
        :param value: valuer recherché
        :return: Retourne un domain de recherche correspondant à la recherche sur le champ calculé is_valid
        """
        computed_today = fields.Date.today()
        search_domain = []
        if (operator == '=' and value is True) or (operator == '!=' and value is False):
            search_domain = [
                '&',
                '|', ('begin_date', '=', False), ('begin_date', '<=', computed_today),
                '|', ('end_date', '=', False), ('end_date', '>=', computed_today)
            ]
        elif (operator == '=' and value is False) or (operator == '!=' and value is True):
            search_domain = [
                '!',
                '&',
                '|', ('begin_date', '=', False), ('begin_date', '<=', computed_today),
                '|', ('end_date', '=', False), ('end_date', '>=', computed_today)
            ]
        return search_domain

    # endregion

    # region Constrains and Onchange
    @api.constrains('begin_date', 'end_date')
    def _check_date(self):
        """Check if the begin_date is valid."""
        for rec in self:
            if rec.begin_date and rec.end_date and rec.begin_date > rec.end_date:
                raise ValidationError(_("Beginning date must be inferior to ending date"))

    @api.onchange('begin_date')
    def _onchange_begin_date(self):
        """Check on the fly the validity of begin_date and if not, set its value.

        to one day before end_date and display a warning
        """
        if self.begin_date and self.end_date and self.begin_date > self.end_date:
            self.begin_date = fields.Date.to_string(fields.Date.from_string(self.end_date) + relativedelta(days=-1))
            return {
                'warning': {
                    'title': _('Warning : wrong value'),
                    'message': _("The beginning date must be inferior to the ending date")
                }
            }

    @api.onchange('end_date')
    def _onchange_end_date(self):
        """Check on the fly the validity of end_date and if not, set its value.

        to one day after begin_date and display a warning
        """
        if self.begin_date and self.end_date and self.begin_date > self.end_date:
            self.end_date = fields.Date.to_string(fields.Date.from_string(self.begin_date) + relativedelta(days=+1))
            return {
                'warning': {
                    'title': _('Warning : wrong value'),
                    'message': _("The ending date must be superior to the beginning date")
                }
            }

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_open_foyer_form(self):
        """Display the form view of a foyer."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('partner_type_foyer.horanet_foyer_view_form').id,
            'target': 'current',  # current / new
            'res_id': self.foyer_id.id,
        }

    @api.multi
    def action_open_partner_form(self):
        """Display the form view of a partner."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': self.env.ref('partner_type_foyer.view_citizen_form').id,
            'target': 'current',  # current / new
            'res_id': self.partner_id.id,
        }

    # endregion

    # region Model methods
    # endregion
    pass
