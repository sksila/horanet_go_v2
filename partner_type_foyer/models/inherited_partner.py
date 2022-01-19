import base64
import logging
import threading
from datetime import date

from odoo import _, api, exceptions, fields, models, tools
from odoo.modules import get_module_resource
from odoo.osv.expression import get_unaccent_wrapper

ABRIDGED_NAME_SIZE = 64
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    company_type = fields.Selection(selection_add=[('foyer', "Foyer")], store=True)

    fixed_name = fields.Char(string='Fixed name')
    foyer_name = fields.Char(string='Foyer full name', compute='_compute_foyer_name', store=False)
    abridged_display_name = fields.Char(string='Abridged foyer name', compute='_compute_abridged_display_name')

    foyer_relation_ids = fields.One2many(
        string='Foyers',
        comodel_name='horanet.relation.foyer',
        inverse_name='partner_id',
        copy=True)
    foyer_member_ids = fields.One2many(
        string='Foyer members',
        comodel_name='horanet.relation.foyer',
        inverse_name='foyer_id')
    active_member_count = fields.Integer(
        string='Active member count',
        compute='_compute_active_member_count',
        store=False)
    active_foyer_member_ids = fields.One2many(
        string='Current members',
        comodel_name='res.partner',
        compute='_compute_active_foyer_members',
        store=False)

    # search fields
    search_field_foyer_member = fields.Char(
        string='Search foyer by member name',
        compute=lambda x: '',
        search='_search_foyer_by_member_name',
        store=False)
    search_field_foyer_address = fields.Char(
        string='Search foyer by member address',
        compute=lambda x: '',
        search='_search_foyer_by_member_address',
        store=False)
    search_field_all_foyers_members = fields.One2many(
        string='Related partners from foyer',
        compute=lambda x: '',
        comodel_name='res.partner',
        search='_search_field_all_foyers_members',
        store=False)

    # endregion

    # endregion

    # region Fields method
    @api.depends('foyer_member_ids')
    def _compute_company_type(self):
        """Override :meth:`_compute_company_type` to take the new value 'foyer' in charge.

        :return: nothing
        """
        if self.env.context.get('onchange_company_type') == 'foyer':
            # in case the company_type was changed via onchange, self is a record and compute is not necessary
            self.company_type = 'foyer'
        elif self.env.context.get('default_company_type') == 'foyer':
            # fix the broken default value on the computed field
            for partner in self:
                partner.company_type = 'foyer'
        else:
            partner_type_foyer = self.filtered(lambda p: p.foyer_member_ids or p.company_type == 'foyer')
            for partner in partner_type_foyer.filtered(lambda p: p.company_type != 'foyer'):
                # Only change company_type if necessary
                partner.company_type = 'foyer'
            # call the other override methods only on the records not type foyer
            super(ResPartner, self - partner_type_foyer)._compute_company_type()

    def _write_company_type(self):
        """Override the inverse method of company_type to take the new value 'foyer' in charge."""
        partner_type_foyer = self.filtered(lambda p: p.foyer_member_ids or p.company_type == 'foyer')
        for partner in partner_type_foyer:
            partner.is_company = partner.company_type == 'foyer'
            super(ResPartner, self - partner)._write_company_type()

    @api.model
    def _search_foyer_by_member_name(self, operator, value):
        """Search foyer by member name.

        :param operator: search operator
        :param value: searched value
        :return: a domain that filters on the id field
        """
        search_name = value
        if operator in ('ilike', 'like'):
            search_name = '%%%s%%' % value
        if operator in ('=ilike', '=like'):
            operator = operator[1:]

        ids = self._get_foyer_id_by_member_name(search_name, operator)
        return [('id', 'in', ids)]

    @api.model
    def _search_foyer_by_member_address(self, operator, value):
        """Search all partner type foyer with a member with specific address.

        :param operator: search operator
        :param value: searched value
        :return: a domain that filters on the id field
        """
        if not isinstance(value, str):
            return []

        search_name = '%%%s%%' % value

        res_domain = ['|', '|', '|', '|', '|',
                      ('street', operator, search_name),
                      ('street2', operator, search_name),
                      ('zip', operator, search_name),
                      ('city', operator, search_name),
                      ('country_id.name', operator, search_name),
                      ('state_id.name', operator, search_name), ]

        return [('id', 'in', self.search(res_domain).mapped('foyer_relation_ids.foyer_id.id'))]

    @api.depends('foyer_member_ids', 'company_type')
    def _compute_active_member_count(self):
        """Compute the number of active citizen in a foyer."""
        for rec in self:
            if rec.company_type == 'foyer':
                rec.active_member_count = len(rec.foyer_member_ids)

    @api.depends('foyer_relation_ids')
    def _compute_active_foyer_members(self):
        """Compute the number of active citizen in a family."""
        for rec in self:
            foyer_relation_ids = rec.foyer_relation_ids.search_read(
                [('foyer_id', '=', rec.id), ('is_valid', '=', True)],
                ['partner_id']
            )

            partner_ids = [f['partner_id'][0] for f in foyer_relation_ids]

            rec.active_foyer_member_ids = self.search(
                [('id', 'in', partner_ids)]
            )

    @api.depends('foyer_relation_ids', 'fixed_name', 'company_type')
    def _compute_foyer_name(self):
        """Compute the foyer name, based on the list of the current active members.

        :return: the foyer name
        """
        empty_firstname = '( )'
        for rec in self:
            foyer_name = False
            if rec.company_type == 'foyer':
                foyer_name = u'Foyer'
                if rec.fixed_name:
                    foyer_name = rec.fixed_name
                elif rec.active_foyer_member_ids and len(rec.active_foyer_member_ids.ids) > 0:
                    dict_name = {}
                    for partner in rec.active_foyer_member_ids:
                        if partner.lastname in dict_name:
                            dict_name[partner.lastname].append(partner.firstname or empty_firstname)
                        else:
                            dict_name[partner.lastname] = [partner.firstname or empty_firstname]
                    for lastname, firstnames in dict_name.items():
                        foyer_name += ' ' + lastname + ' ' + u', '.join(firstnames)
            rec.foyer_name = foyer_name

    @api.depends('company_type', 'foyer_name')
    def _compute_abridged_display_name(self):
        """Truncate the display name if longer than 64 characters."""
        for rec in self:
            result = rec.name
            if rec.company_type == 'foyer':
                result = rec.foyer_name
            # elif rec.company_type == 'residence':
            #     result = rec.residence_name
            if result and len(result) >= ABRIDGED_NAME_SIZE > 4:
                result = result[0:ABRIDGED_NAME_SIZE - 3] + '...'
            rec.abridged_display_name = result

    # Fonction de recherche de relation par foyer grâce à l'id d'un partner
    @api.model
    def _search_field_all_foyers_members(self, operator, value):
        """Allow us to retrieve partners for specific foyer.

        :param operator: search operator
        :param value: searched value
        :return: a domain that filters on the id field
        """
        arg = value
        if isinstance(value, str):
            if value.isdigit():
                arg = int(value)
            else:
                arg = False
        relation_foyer_ids = self.browse(arg) \
            .filtered('foyer_relation_ids.is_valid') \
            .mapped('foyer_relation_ids.foyer_id.foyer_member_ids.partner_id') \
            .filtered('foyer_relation_ids.is_valid').ids

        return [('id', 'in', relation_foyer_ids)]

    # endregion

    # region Constrains and Onchange
    @api.multi
    @api.onchange('company_type')
    def onchange_company_type(self):
        """Use to change the value of is_company field based on company_type.

        :return: nothing
        """
        if self.company_type == 'foyer':
            # add a context key to remove indetermination in case of onchange on the
            # compute method bound to company_type
            self.env.context = self.with_context(onchange_company_type='foyer').env.context
            if not self.is_company:
                # Only change if necessary
                self.is_company = True
        else:
            # call the override method only if partner not type foyer
            super(ResPartner, self).onchange_company_type()

    @api.multi
    @api.constrains('company_type', 'is_company')
    def _check_company_type_foyer(self):
        """Check if company_type foyer is valid.

        :raise: openerp.exceptions.ValidationError a partner of type of foyer or residence isn't a company
        """
        for rec in self:
            if rec.company_type == 'foyer' and not rec.is_company:
                raise exceptions.ValidationError(_("Error a foyer or need to be flagged as a company"))

    # endregion

    # region CRUD (overrides)
    @api.model
    def default_get(self, fields_list):
        """Override default_get methode to get the default membre adress from adress of the foyer responsible."""
        res = super(ResPartner, self).default_get(fields_list)
        foyer_id = self.env.context.get('get_default_address_from_foyer', False)
        if not foyer_id:
            return res
        # si le foyer existe cad  isinstance(foyer_id, int) = True
        if foyer_id and isinstance(foyer_id, int):
            foyer_id = self.env["res.partner"].browse(foyer_id)
            if len(foyer_id.foyer_member_ids):
                responsabes_id = foyer_id.foyer_member_ids.filtered(lambda p: p.partner_id.is_responsible)
                if len(responsabes_id):
                    responsabe_id = responsabes_id[0].partner_id
                    adress = self.env["res.partner"].search_read(
                        domain=[("id", "=", responsabe_id.id)],
                        fields=self.get_default_address_from_foyer_fields(),
                    )
                if adress and adress[0]:
                    adress = adress[0]
                    del adress["id"]
                    res.update(adress)
                    return res
        return res

    @api.model
    def create(self, vals):
        """Override create methode to add a default foyer image if necessary."""
        if not vals.get('image') and vals.get('company_type', self.env.context.get('default_company_type')) == 'foyer':
            vals['image'] = self._get_default_image_foyer(vals.get('type'), vals.get('parent_id'))

        return super(ResPartner, self).create(vals)

    @api.model
    def name_search(self, name, args=[], operator='ilike', limit=10):
        u"""Surcharge de la méthode de recherche.

        Prend en compte les particularités des partners de type foyer,
        pour lesquels la recherche s'effectue en fonction des membres
        """
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)
            # Liste des id de partners correspondant à la recherche
            partner_ids = []

            # Recherche des partners standard
            partner_ids.extend(self.search([('company_type', '=', 'person'),
                                            '|',
                                            ('email', operator, unaccent(search_name)),
                                            ('display_name', operator, unaccent(search_name))
                                            ], limit=limit).ids)
            # Recherche dans les foyers
            partner_ids.extend(self._get_foyer_id_by_member_name(search_name, operator, limit=limit, active=False))

            # TODO: NEED TO BE MOVED IN partner_type_residence
            # Recherche dans les résidences
            # partner_ids.extend(
            #     self._get_residence_id_by_member_name(search_name, operator, limit=limit, active=False)
            # )
            # Suppression des doublons
            partner_ids = list(set(partner_ids))
            # Appel de la recherche standard pour prendre en compte les éventuels args + gestion des la sécurité
            ids = self.search([('id', 'in', partner_ids)] + args, limit=limit).ids
            if ids:
                return self.browse(ids).name_get()
            else:
                return []
        return super(ResPartner, self).name_search(name, args, operator=operator, limit=limit)

    # endregion

    # region Actions
    @api.multi
    def action_add_foyer(self):
        """Create a new foyer for the partner and add him to it."""
        for rec in self:
            if not rec.foyer_relation_ids:
                new_foyer_rec = rec.create({
                    'company_type': 'foyer',
                    'is_company': True,
                    'name': 'Foyer'
                })
                new_rel_foyer_rec = rec.env['horanet.relation.foyer'].create({
                    'partner_id': rec.id,
                    'foyer_id': new_foyer_rec.id,
                    'is_responsible': True,
                })
                rec.foyer_relation_ids = [(4, new_rel_foyer_rec.id)]

    # endregion

    # region Model methods
    def get_default_address_from_foyer_fields(self):
        return [
            "zip_id", "city_id",
            "street_number_id", "street_id",
            "street2", "street2",
            "street3", "state_id",
            "country_id"
        ]

    @api.multi
    def name_get(self):
        """Return a textual representation for the records in ``self``.

        name_get() -> [(id, name), ...].

        By default this is the value of the ``display_name`` field.

        :return: list of pairs ``(id, text_repr)`` for each records
        :rtype: list(tuple)
        """
        foyer_partners = self.filtered(lambda x: x.company_type == 'foyer')
        normal_partners = self - foyer_partners

        result = super(ResPartner, normal_partners).name_get()
        for record in foyer_partners:
            if record.company_type == 'foyer':
                result.append((record.id, record.foyer_name))
        return result

    @api.model
    def _get_foyer_id_by_member_name(self, search_term, operator, where_clause=None, active=True, limit=100):
        u"""Recherche SQL des partners de type foyer OU résidence par le nom des membres.

        :param search_term: Terme à rechercher dans le nom des membres
        :param operator: Opérateur de comparaison SQL
        :param where_clause: Optionel, clause de recherche SQL (sans le "where")
        :param limit: limit SQL
        :param active: Default : True, Indique si la recherche s'effectue sur les membres actifs
        :param company_type: "foyer" OU "residence" indique si l'on recherche sur les foyers ou résidences
        :return: list des ids de partners
        """
        cr = self.env.cr
        company_type = 'foyer'
        unaccent = get_unaccent_wrapper(cr)
        active_clause = None
        if active:
            active_clause = """ (relation.begin_date is null OR relation.begin_date <= %s)
                                        AND
                                        (relation.end_date is null OR relation.end_date >= %s)"""
        query = """
                    SELECT distinct foyer.id from res_partner as partner
                        INNER JOIN HORANET_RELATION_FOYER as relation
                            ON partner.id = relation.partner_id
                            {where_clause} {active_clause}
                        INNER JOIN res_partner as foyer
                            ON relation.foyer_id = foyer.id and foyer.company_type = '{company_type}'
                    WHERE  (foyer.active = True)
                        AND (foyer.company_type = '{company_type}')
                        AND ({firstname} {operator} {term}
                            OR {lastname} {operator} {term}
                            OR foyer.fixed_name {operator} {term})
                    """.format(where_clause=(where_clause and ("AND %s" % where_clause) or ''),
                               operator=operator,
                               firstname=unaccent('partner.firstname'),
                               lastname=unaccent('partner.lastname'),
                               fixed_name=unaccent('foyer.fixed_name'),
                               term=unaccent('%s'),
                               company_type=company_type,
                               active_clause=(active_clause and ("AND %s" % active_clause) or ''))
        if limit:
            query += " limit " + str(limit)
        sqlparams = [search_term, search_term, search_term]
        if active:
            sqlparams = [date.today(), date.today()] + sqlparams
        cr.execute(query, sqlparams)
        ids = list(set([x[0] for x in cr.fetchall()]))
        return ids

    @api.model
    def _get_foyer_id_by_address_name(self, search_term, operator, where_clause=None, limit=100):
        cr = self.env.cr
        unaccent = get_unaccent_wrapper(cr)
        query = """ SELECT distinct relation.foyer_id from res_partner as partner
                    INNER JOIN HORANET_RELATION_FOYER relation
                        ON partner.id = relation.partner_id {where}
                    INNER JOIN res_street_number as street_number
                        ON partner.street_number_id = street_number.id
                        AND (partner.{city} {operator} {percent}
                            OR partner.{zip} {operator} {percent}
                            OR partner.{street} {operator} {percent}
                            OR street_number.name {operator} {percent})
                    limit {limit}
                """.format(where=(where_clause and ("AND %s" % where_clause) or ''),
                           operator=operator,
                           city=unaccent('city'),
                           zip=unaccent('zip'),
                           street=unaccent('street'),
                           percent=unaccent('%s'),
                           limit=limit)
        cr.execute(query, [search_term, search_term, search_term, search_term])
        ids = list(set([x[0] for x in cr.fetchall()]))
        return ids

    @api.model
    def _get_default_image_foyer(self, partner_type, parent_id):
        if getattr(threading.currentThread(), 'testing', False) or self._context.get('install_mode'):
            return False

        colorize, img_path, image = False, False, False
        if partner_type not in ['invoice', 'delivery', 'other'] and not parent_id:
            img_path = get_module_resource('partner_type_foyer', 'static/src/img', 'community-people.png')
            colorize = True
            with open(img_path, 'rb') as f:
                image = f.read()
            if image and colorize:
                image = tools.image_colorize(image)

        return image and tools.image_resize_image_big(base64.b64encode(image)) or False

    @api.multi
    def get_foyers_active_members(self, reponsible=False):
        """Return active partners.

        Expect current partner, that are under responsibility (or not), in the foyer(s) of
        current partner

        :param reponsible: filter on partner's responsibility
        :return: partner recordset
        """
        self.ensure_one()

        foyer_relations = self.mapped('foyer_relation_ids')
        if reponsible:
            foyer_relations = foyer_relations.filtered('is_responsible')

        return foyer_relations.mapped('foyer_active_partners').filtered(lambda r: r.id != self.id)

    # endregion

    pass
