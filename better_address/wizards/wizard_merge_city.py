# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from urllib import quote


class WizardMergeCity(models.TransientModel):
    """Manage city merging."""

    # region Private attributes
    _name = 'horanet.wizard.merge.city'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    city_to_merge_id = fields.Many2one(
        string="City to merge",
        comodel_name='res.city',
        required=False,
        readonly=True,
    )

    city_renamed = fields.Char(string="City renamed", compute='_compute_city_renamed')
    use_name = fields.Boolean(string="Use name", default=True, readonly=True)
    city_to_merge_zip_ids = fields.Many2many(
        string="City to merge zips",
        related='city_to_merge_id.zip_ids',
        readonly=True,
    )
    city_to_merge_code = fields.Char(string="City to merge code", related='city_to_merge_id.code', readonly=True)
    use_code = fields.Boolean(string="Use code", default=False)

    city_to_merge_state_id = fields.Many2one(
        string="City to merge state",
        related='city_to_merge_id.country_state_id',
        readonly=True,
    )
    use_state_id = fields.Boolean(string="Use state", default=True)

    city_to_merge_country_id = fields.Many2one(
        string="City to merge country",
        related='city_to_merge_id.country_id',
        readonly=True)
    use_country_id = fields.Boolean(string="Use country", default=True)

    use_zip_ids = fields.Many2many(
        string="Use zip codes",
        comodel_name='res.zip',
        store=False,
        domain="[('id', 'in', city_to_merge_zip_ids and city_to_merge_zip_ids[0][2] or [])]",
    )
    similar_city_ids = fields.Many2many(
        string="Similar cities",
        comodel_name='res.city',
        compute='_get_similar_cities',
    )
    city_merge_destination_id = fields.Many2one(
        string="Merge destination",
        comodel_name='res.city',
        domain="['&', ('id', 'in', similar_city_ids and similar_city_ids[0][2] or []), ('state', '=', 'confirmed')]",
    )
    number_partner_with_city_id = fields.Integer(
        string="Partners referencing this city :",
        compute='_compute_number_partner_with_city_id',
    )
    similarity_threshold = fields.Selection(
        string="Similarity",
        default='3',
        selection=[('1', 'Low'), ('3', 'Normal'), ('4', 'High'), ('6', 'Highest')],
    )

    new_name = fields.Char(
        string="City name",
        compute='_get_default_city_information',
        store=True,
        readonly=False,
    )
    new_code = fields.Char(
        string="City Code",
        size=64,
        store=True,
        readonly=False,
        compute='_get_default_city_information',
        help="The official code for the city")
    new_zip_ids = fields.Many2many(
        string="ZIP codes",
        comodel_name='res.zip',
        store=True,
        readonly=False,
        compute='_get_default_city_information',
    )
    new_country_state_id = fields.Many2one(
        string="State",
        comodel_name='res.country.state',
        store=True,
        readonly=False,
        compute='_get_default_city_information',
        domain="[('country_id', '=?', new_country_id)]",
    )
    new_country_id = fields.Many2one(
        string="Country",
        store=True,
        readonly=False,
        compute='_get_default_city_information',
        comodel_name='res.country',
    )

    old_code = fields.Char(string="Code", readonly=True, related='city_merge_destination_id.code')
    old_zip_ids = fields.Many2many(string="Zip code", readonly=True, related='city_merge_destination_id.zip_ids')
    old_country_id = fields.Many2one(string="Country", readonly=True, related='city_merge_destination_id.country_id')
    old_country_state_id = fields.Many2one(
        string="State",
        readonly=True,
        related='city_merge_destination_id.country_state_id')

    # endregion

    # region Fields method
    @api.depends('city_to_merge_id')
    def _compute_use_zip_ids(self):
        """Initialize the list of city to merge zip."""
        self.use_zip_ids = self.city_to_merge_id.zip_ids.ids

    @api.depends('city_to_merge_id')
    def _compute_number_partner_with_city_id(self):
        """Count the number of partner referencing the city to merge."""
        self.number_partner_with_city_id = self.env['res.partner'].search_count(
            [('city_id', '=', self.city_to_merge_id.id)])

    @api.depends('city_to_merge_id')
    def _compute_city_renamed(self):
        """Initialize the city name used to search similar cities."""
        self.city_renamed = self.city_to_merge_id.name

    @api.depends('city_to_merge_id')
    def _get_default_city_information(self):
        """Initialize the city to merge information fields."""
        self.new_name = self.city_to_merge_id.name.upper()
        self.new_code = self.city_to_merge_id.code
        self.new_zip_ids = self.city_to_merge_id.zip_ids
        self.new_country_state_id = self.city_to_merge_id.country_state_id
        self.new_country_id = self.city_to_merge_id.country_id

    @api.depends('city_to_merge_id', 'city_renamed', 'use_zip_ids', 'use_name', 'use_country_id',
                 'use_state_id', 'use_code', 'similarity_threshold')
    def _get_similar_cities(self):
        """Search method used to find cities based on a "fuzzy" name."""
        search_domain = [('id', '!=', self.city_to_merge_id.id)]
        if not self.city_renamed:
            return None
        else:
            search_domain.append(('name', '%', self.city_renamed))
        if self.use_zip_ids:
            search_domain.append(('zip_ids', 'in', self.use_zip_ids.ids))
        if self.use_country_id and self.city_to_merge_country_id:
            search_domain.append(('country_id', '=', self.city_to_merge_country_id.id))
        if self.use_state_id and self.city_to_merge_state_id:
            search_domain.append(('country_state_id', '=', self.city_to_merge_state_id.id))
        if self.use_code and self.city_to_merge_code:
            search_domain.append(('code', '=', self.city_to_merge_code))

        if self.similarity_threshold != '3':
            # 0.3 is the default PSQL limit, it seems to be reset at each transaction
            # https://www.postgresql.org/docs/current/pgtrgm.html
            self.env.cr.execute('SELECT set_limit({limit:0.1f})'.format(limit=float(self.similarity_threshold) / 10))
        self.similar_city_ids = self.similar_city_ids.search(search_domain)

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_merge_city(self):
        u"""
        Fusion de ville.

        La ville source est supprimé au profit de la ville de destination, en tenant compte
        des éventuel partenaires possédant l'addresse qui va être fusionnée.
        """
        self.ensure_one()
        if not self.city_merge_destination_id:
            raise exceptions.ValidationError(_("Missing city, the merge need a destination"))

        if self.city_to_merge_id.zip_ids:
            # attention l'ordre est important
            self.city_to_merge_id.zip_ids.write({'city_ids': [(4, self.city_merge_destination_id.id)]})
            self.city_to_merge_id.zip_ids.write({'city_ids': [(3, self.city_to_merge_id.id)]})

        referencing_street_rec = self.env['res.street'].search([('city_id', '=', self.city_to_merge_id.id)])
        # dé-référencement des rue de la ville à fusionner
        if referencing_street_rec:
            referencing_street_rec.write({'city_id': self.city_merge_destination_id.id})

        referencing_partner_rec = self.env['res.partner'].search([('city_id', '=', self.city_to_merge_id.id)])
        if referencing_partner_rec:
            # Modification des addresses de partenaire basé sur la ville à supprimer (fusionner)
            new_address = {'city_id': self.city_merge_destination_id.id}
            if self.city_merge_destination_id.country_id:
                new_address['country_id'] = self.city_merge_destination_id.country_id.id
            if self.city_merge_destination_id.country_state_id:
                new_address['state_id'] = self.city_merge_destination_id.country_state_id.id
            # Modification des adresses existante
            referencing_partner_rec.write(new_address)

            for partner in referencing_partner_rec:
                if not partner.zip_id and self.city_merge_destination_id.zip_ids:
                    # Si pas de code postal, on ajoute celui de la ville
                    partner.zip_id = self.city_merge_destination_id.zip_ids[0].id
                elif partner.zip_id and not self.city_merge_destination_id.zip_ids:
                    # Si la ville n'a pas de code postal, on enlève celui du partner
                    partner.zip_id = None
                elif partner.zip_id and self.city_merge_destination_id.zip_ids:
                    if partner.zip_id not in self.city_merge_destination_id.zip_ids:
                        # Si le code postal du partenaire ne fait pas parti de ceux de la ville, on le remplace
                        partner.zip_id = self.city_merge_destination_id.zip_ids[0].id

        self.city_to_merge_id.unlink()

        return self._open_city_view_form(self.city_merge_destination_id, target='current')

    @api.multi
    def action_add_city_to_referential(self):
        u"""
        Ajout de la ville à fusionner au référentiel.

        Dans le cas ou la ville n'est effectivement pas un doublon, les info requises sont renseignées afin d'ajouter
        la ville au référentiel.
        """
        self.ensure_one()
        if not self.new_country_id:
            raise exceptions.ValidationError(_("A country is required"))
        if not self.new_name:
            raise exceptions.ValidationError(_("A name is required"))

        is_french = self.new_country_id == self.env.ref('base.fr')
        if is_french:
            if not self.new_country_state_id:
                raise exceptions.ValidationError(_("A country state is required in case of french city !"))
            if not self.new_zip_ids:
                raise exceptions.ValidationError(_("One or more zip code are required in case of french city !"))

        if self.new_country_state_id and self.new_country_state_id.country_id != self.new_country_id:
            raise exceptions.ValidationError(_("The selected country state does not belong to the selected country"))

        self.city_to_merge_id.write({
            'name': self.new_name,
            'state': 'confirmed',
            'code': self.new_code,
            'zip_ids': [(6, 0, self.new_zip_ids.ids)],
            'country_state_id': self.new_country_state_id.id,
            'country_id': self.new_country_id.id,
        })

        return self._open_city_view_form(self.city_to_merge_id, target='main')

    @api.multi
    def action_open_qwant_query(self):
        """Open a new tab, on a Qwant search."""
        query_string = '{city_name} {country_name} {country_state} {zip_code}'.format(
            city_name=self.city_to_merge_id and self.city_to_merge_id.name or '',
            country_name=self.city_to_merge_country_id and self.city_to_merge_country_id.name or '',
            country_state=self.city_to_merge_state_id and self.city_to_merge_state_id.name or '',
            zip_code=self.city_to_merge_zip_ids and self.city_to_merge_zip_ids[0].name or '',
        )

        return {
            'type': 'ir.actions.act_url',
            'url': 'https://www.qwant.com/?q=' + quote(query_string),
            'target': 'new',
        }

    # endregion

    # region Model methods
    def _open_city_view_form(self, city, target='new'):
        """Action to open city form view."""
        return {
            'context': self.env.context,
            'res_model': city._name,
            'type': 'ir.actions.act_window',
            'res_id': city.id,
            'view_mode': 'form',
            'target': target,
        }

    # endregion

    pass
