import psycopg2
import logging
from odoo import models, fields, api, exceptions, _
from ..config import config

_logger = logging.getLogger(__name__)
city_import_count = 0


class HoranetCity(models.Model):
    # region Private attributes
    _name = "res.city"
    _inherit = ['mail.thread', ]
    _order = "name asc"
    _rec_name = "display_name"  # _rec_name override by name_get
    _sql_constraints = [('unicity_on_code', 'UNIQUE(code)', _('The city code must be unique if not null'))]
    # endregion

    # region Default methods
    # endregion
    # region Fields declaration
    display_name = fields.Char(string='Name', compute='_get_display_name', store=False)
    name = fields.Char(string='City name', required=True)
    state = fields.Selection(string='Status', selection=config.STATES_LIST, default='draft')
    code = fields.Char(string='City Code', size=64, help="The official code for the city")
    zip_ids = fields.Many2many(string='ZIP codes', comodel_name='res.zip')
    # operator =? pour domain --> compare if exist.
    # http://stackoverflow.com/questions/29442993/available-domain-operator-in-openerp-odoo
    country_state_id = fields.Many2one(
        String='State',
        comodel_name='res.country.state',
        domain="[('country_id', '=?', country_id)]", )
    country_id = fields.Many2one(
        string='Country',
        comodel_name='res.country', )

    # endregion

    # region Fields method
    @api.multi
    @api.depends('name', 'code', 'country_state_id', 'country_id', )
    def _get_display_name(self):
        """Create the display name of the city."""
        for rec in self:
            if rec.code:
                name = [rec.code, rec.name]
            else:
                name = [rec.name]
            if rec.country_state_id:
                name.append(rec.country_state_id.name)
            if rec.country_id:
                name.append(rec.country_id.name)
                rec.display_name = ', '.join(name)

    # endregion

    # region Constrains and Onchange
    @api.constrains('country_state_id', 'country_id')
    def _check_coherence_country(self):
        self.ensure_one()
        if self.country_state_id and self.country_id and self.country_state_id.country_id != self.country_id:
            raise exceptions.ValidationError(
                _("The state {state_name} does not exist in this country ({country_name})").format(
                    state_name=self.country_state_id.name,
                    country_name=self.country_id.name
                ))

    @api.onchange('country_state_id')
    def onchange_country_state_id(self):
        """Set the country_id corresponding to the country of the country state."""
        if self.country_state_id:
            self.country_id = self.country_state_id.country_id

    # endregion

    # region CRUD (overrides)
    @api.multi
    def write(self, vals):
        """Override write to correct values, before being stored."""
        if 'name' in vals:
            vals['name'] = vals['name'].upper()

        if not vals.get('country_id', True):
            # if the country_id will be deleted
            if vals.get('country_state_id', self.country_state_id):
                # if the record will have OR has a country_state, then the country_id will
                # be forced to match the country_id of the state
                country_id = False
                if vals.get('country_state_id'):
                    state_recs = self.country_state_id.browse([vals.get('country_state_id')])
                    if len(state_recs) > 0:
                        country_id = state_recs[0].country_id.id
                else:
                    country_id = self.country_state_id.country_id.id
                vals['country_id'] = country_id

            self._check_city_unicity(vals)

        return super(HoranetCity, self).write(vals)

    @api.model
    def create(self, vals):
        """Wrapper for the create method.

        It ensures that all valid records are loaded, while records that can't be loaded
        for any reason are left out. Simulate the "psycopg2.Warning"
        """
        context = self.env.context or {}
        if 'name' in vals:
            vals['name'] = vals['name'].upper()
        if vals.get('country_state_id') and not vals.get('country_id'):
            states = self.country_state_id.search([('id', '=', vals.get('country_state_id'))], limit=1)
            if len(states) == 1:
                vals['country_id'] = states[0].country_id.id

        if context.get('install_mode'):
            # install_mode : semble être l'équivalent du mode de création par import
            if context.get('trace_progression') and context.get('nb_rec'):
                global city_import_count
                city_import_count += 1
                # nb_done = context.get('nb_rec_done') or 0
                # self.env.context = self.with_context(nb_rec_done=(nb_done + 1)).env.context
                #     self.env.nb_rec_done = self.env.nb_rec_done + 1 if hasattr(self.env, 'nb_rec_done') else 1
                if (city_import_count % 100) == 0:
                    _logger.info("Processing record {0} of {1}".format(city_import_count, context.get('nb_rec')))
            if vals.get('country_state_id') and not vals.get('country_id'):
                states = self.env['res.country.state'].search([('id', '=', vals.get('country_state_id'))], limit=1)
                if len(states) == 1:
                    vals['country_id'] = states[0].country_id.id
                else:
                    raise psycopg2.Warning("City.code : " + str(vals.get('city_code')) + " not found")
                    # raise Warning("City.code : " + str(vals.get('city_code')) + " not found")
            if 'state' not in vals:
                vals['state'] = 'confirmed'
        else:
            self._check_city_unicity(vals)
            if vals.get('code'):
                duplicate_city = self.search(args=[('code', '=', vals.get('code'))], limit=1)
                if len(duplicate_city) > 0:
                    raise exceptions.ValidationError(self.get_unicity_error_message(duplicate_city[0]))
        return super(HoranetCity, self).create(vals)

    @api.model
    def load(self, import_fields, data):
        """Wrapper for the load method.

        It ensures that all valid records are loaded, while records that can't be
        loaded for any reason are left out. Returns the failed records ids and error messages.
        """
        if len(data) > 0:
            debug = self.env.ref('base.group_no_one') in self.env.user.groups_id
            global city_import_count
            city_import_count = 0
            return super(HoranetCity, self.with_context(nb_rec=len(data), trace_progression=debug)).load(import_fields,
                                                                                                         data)
        return super(HoranetCity, self).load(import_fields, data)

    @api.multi
    def name_get(self):
        """Override name_get method to add zip. It is used to display the zip and the name.

        in the dropdown in the form view, thus allowing the user to search a city by it's zip
        """
        res = []
        for bzip in self:
            name = [bzip.name]
            res.append((bzip.id, ", ".join(name)))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', context=None, limit=20):
        """Override name_search to add the option to search by zip.

        :return: domain
        """
        if args is None:
            args = []
        if context is None:
            context = {}
        cities = []
        # recherche d'une ville selon son code postal ou son nom (switch sur l'input pour des raison de perf)
        if name:
            if name.isdigit():
                cities = self.search([('zip_ids.name', '=ilike', name + '%')] + args, limit=limit)
            else:
                cities = self.search([('name', 'ilike', name)] + args, limit=limit)
        else:
            cities = self.search(args, limit=limit)

        # if len(ids) >0 and name.isdigit():

        res = []
        # construction de la liste de tuple de résultat en fonction de la nature de la recherche saisie
        for city in self.browse(cities.ids):
            if not city.zip_ids:
                res.append((city.id, city.name))
            else:
                if name.isdigit():
                    if len(city.zip_ids) > 1:
                        res.append((city.id, "(...)  " + city.name))
                    else:
                        res.append((city.id, ", ".join([x.name for x in city.zip_ids]) + ", " + city.name))
                else:
                    if len(city.zip_ids) > 1:
                        res.append((city.id, city.name + "  (...)"))
                    else:
                        res.append((city.id, city.name + " " + ", ".join([x.name for x in city.zip_ids])))

        # tri de la liste des résultats selon la taille de la chaîne (approximation de "best match")
        res.sort(key=lambda ville: len(ville[1]))
        return res

    # endregion

    # region Actions
    @api.multi
    def action_draft(self):
        """Set the city state to draft."""
        self.ensure_one()  # recommandation
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        """Set the city state to confirmed."""
        self.ensure_one()  # recommandation
        self.state = 'confirmed'

    @api.multi
    def action_invalidate(self):
        """Set the city state to invalidated."""
        self.ensure_one()
        self.state = 'invalidated'

    @api.multi
    def action_open_merge_city_wizard(self):
        u"""Appel du wizard de fusion des villes."""
        self.ensure_one()

        # self.state = 'new'
        # wizard_view = self.env.ref('better_address.wizard_merge_city')
        wizard_rec = self.env['horanet.wizard.merge.city'].create({
            'city_to_merge_id': self.id,
        })
        wizard_action = self.env.ref('better_address.wizard_merge_city_action')
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

    # region Model methods
    @api.multi
    def _check_city_unicity(self, vals):
        """This constraint is used to create a message displaying the duplicates cities.

        To help the user correct the city data
        :raise: Validation error if another city exist with the same code
        """
        for rec in self:
            city_code = (vals.get('code') or rec.code)
            if city_code:
                duplicate_city = self.search(args=[('code', '=', city_code), ('id', '!=', rec.id)], limit=1)
                if len(duplicate_city) > 0:
                    raise exceptions.ValidationError(self.get_unicity_error_message(duplicate_city[0]))

    @staticmethod
    def get_unicity_error_message(res_city):
        """Generate an error message.

        :param res_city: le model res.city déjà existant
        :return: Le texte du message d'erreur en cas de conflit d'unicité
        """
        return _('Le code saisi existe déjà pour la ville "{0}"').format(res_city.display_name.encode('utf-8'))

    # endregion
    pass
