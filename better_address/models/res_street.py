import logging

import psycopg2

from odoo import models, fields, api, exceptions, _
from odoo.osv.expression import get_unaccent_wrapper, expression
from ..config import config

_logger = logging.getLogger(__name__)
street_import_count = 0


class HoranetStreet(models.Model):
    """This model represent a street."""

    # region Private attributes
    _name = 'res.street'
    _sql_constraints = [
        ('unicity_on_code', 'UNIQUE(code,city_id)', _('The street code must be unique by city if not null'))]
    _order = 'name'
    _rec_name = 'name'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True, index=True)
    code = fields.Char(string='Street Code', size=64, help="The official code for the street")
    city_id = fields.Many2one(string="Related city", comodel_name='res.city', required=True, ondelete='cascade',
                              index=True)
    city_name = fields.Char(string='City name', store=False, related='city_id.name')
    city_code = fields.Char(string='City code', store=False, related='city_id.code')
    city_country_state = fields.Many2one(string="City Country state", store=False, related='city_id.country_state_id')
    state = fields.Selection(string='Status', selection=config.STATES_LIST, default='draft')

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def copy(self, default=None):
        """Override copy method to add 'Copy of' in the name and eventually a number."""
        self.ensure_one()
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', u"Copy of {}%".format(self.name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.name)
        else:
            new_name = u"Copy of {} ({})".format(self.name, copied_count)

        default['name'] = new_name
        default['code'] = ''
        return super(HoranetStreet, self).copy(default)

    @api.model
    def load(self, import_fields, data):
        """Wrapper for the load method.

        It ensures that all valid records are loaded, while records that can't be loaded
        for any reason are left out.
        Returns the failed records ids and error messages.
        """
        if len(data) > 0:
            debug = self.env.ref('base.group_no_one') in self.env.user.groups_id
            global street_import_count
            street_import_count = 0
            return super(HoranetStreet, self.with_context(nb_rec=len(data), trace_progression=debug)).load(
                import_fields,
                data)
        return super(HoranetStreet, self).load(import_fields, data)

    # endregion

    # region Model methods
    # endregion

    # region CRUD

    @api.multi
    def write(self, vals):
        """Override write to correct values, before being stored."""
        self._check_street_unicity(vals)
        return super(HoranetStreet, self).write(vals)

    @api.model
    def create(self, vals):
        """Wrapper for the create method.

        It ensures that all valid records are loaded, while records that can't be loaded
        for any reason are left out. Simulate the "psycopg2.Warning"
        EXEMPLE issue de base partner sequence (OCA)
        """
        context = self.env.context or {}
        if context.get('install_mode'):
            if context.get('trace_progression') and context.get('nb_rec'):
                global street_import_count
                street_import_count += 1
                # nb_done = context.get('nb_rec_done') or 0
                # self.env.context = self.with_context(nb_rec_done=(nb_done + 1)).env.context
                #     self.env.nb_rec_done = self.env.nb_rec_done + 1 if hasattr(self.env, 'nb_rec_done') else 1
                if (street_import_count % 100) == 0:
                    _logger.info("Processing record {0} of {1}".format(street_import_count, context.get('nb_rec')))
            if vals.get('city_code'):
                # install_mode : semble être l'équivalent du mode de création par import
                ir_model_city = self.env['res.city']
                city_ids = ir_model_city.search([('code', '=', vals.get('city_code'))], limit=1)
                if len(city_ids) == 1:
                    vals['city_id'] = city_ids[0].id
                else:
                    raise psycopg2.Warning("City.code : " + str(vals.get('city_code')) + " not found")
                    # raise Warning("City.code : " + str(vals.get('city_code')) + " not found")
            if u'state' not in vals:
                vals[u'state'] = 'confirmed'
        else:
            self._check_street_unicity(vals)
            if vals.get('city_id') and vals.get('code'):
                duplicate_street = next((street for street in
                                         self.search([('code', '=', vals.get('code')),
                                                      ('city_id', 'in', [vals.get('city_id')])],
                                                     limit=1)), None)
                if duplicate_street:
                    raise exceptions.ValidationError(self.get_unicity_error_message(duplicate_street[0]))
        return super(HoranetStreet, self).create(vals)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Override name_search to manually construct the query to get results and get rid of the 'order by'."""
        self.check_access_rights('read')

        # search on the name of the street
        search_name = name
        if operator in ('ilike', 'like'):
            search_name = '%%%s%%' % name
        if operator in ('=ilike', '=like'):
            operator = operator[1:]
        cr = self.env.cr
        unaccent = get_unaccent_wrapper(cr)

        query = "SELECT id FROM res_street where {name} {operator} {term} ".format(
            operator=operator,
            name=unaccent('name'),
            term=unaccent('%s'))

        where_clause_params = [search_name]

        # Ajout d'un éventuel domain dans la clause where de la recherche SQL
        # TODO : tenir compte des jointure sur tables externe (en cas de domain sur modèles liés)
        if args:
            exp = expression(args, self)
            where_clause, where_params = exp.to_sql()
            where_clause = where_clause and [where_clause] or []
            query += (' AND ' if where_clause else '') + ' AND '.join(where_clause)
            where_clause_params += where_params

        if limit:
            query += ' limit %s'
            where_clause_params.append(limit)
        cr.execute(query, where_clause_params)
        ids = map(lambda x: x[0], cr.fetchall())

        if ids:
            list_street = []
            for street in self.browse(ids):
                list_street.append((street.id, street.name + ' (' + street.city_id.name + ')'))
            return sorted(list_street, key=lambda x: x[1])
        else:
            return []

    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'draft')]
    # endregion

    # region Actions
    @api.multi
    def action_draft(self):
        """Set the street state to draft."""
        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        """Set the street state to confirmed."""
        self.ensure_one()
        self.state = 'confirmed'

    @api.multi
    def action_invalidate(self):
        """Set the street state to invalidated."""
        self.ensure_one()
        self.state = 'invalidated'

    @api.multi
    def action_open_merge_street_wizard(self):
        u"""Appel du wizard de fusion des rue."""
        self.ensure_one()

        # self.state = 'new'
        # wizard_view = self.env.ref('better_address.wizard_merge_city')
        wizard_rec = self.env['horanet.wizard.merge.street'].create({
            'street_to_merge_id': self.id,
        })
        wizard_action = self.env.ref('better_address.wizard_merge_street_action')
        return {
            'context': self.env.context,
            'type': wizard_action.type,
            'res_model': wizard_action.res_model,
            'res_id': wizard_rec.id,
            'view_mode': wizard_action.view_mode,
            'target': wizard_action.target,
            'view_type': wizard_action.view_type,
        }
    # endregion

    # region Business
    @api.multi
    def _check_street_unicity(self, vals):
        """Constrain to check the unicity of the street.

        :raise ValidationError: if a street has the same street_code and city_code
        """
        for rec in self:
            street_code = (vals.get('code') or rec.code)
            city_code = (vals.get('city_code') or rec.city_code)
            if street_code or city_code:
                duplicate_street = next((street for street in self.search(
                    args=[('code', '!=', False), ('code', '=', street_code),
                          ('city_code', '=', city_code), ('id', '!=', rec.id)], limit=1)), None)
                if duplicate_street:
                    raise exceptions.ValidationError(self.get_unicity_error_message(duplicate_street[0]))

    @api.multi
    def get_unicity_error_message(self, res_street):
        """Error message related to unicity constrain method."""
        self.ensure_one()
        return _("The specified code already exist for the street '{0}', and the city '{1}'").format(
            res_street.name, res_street.city_id.name)

    # endregion

    pass
