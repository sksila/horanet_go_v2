# -*- coding: utf-8 -*-

from urllib import quote_plus

from odoo import models, fields, api, exceptions, _


class WizardMergeStreet(models.TransientModel):
    """Manage street merging."""

    # region Private attributes
    _name = 'horanet.wizard.merge.street'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    street_to_merge_id = fields.Many2one(
        string="street to merge",
        comodel_name='res.street',
        required=False,
        readonly=True,
    )

    street_renamed = fields.Char(string="Street renamed", compute='_compute_street_renamed')
    use_name = fields.Boolean(string="Use name", default=True, readonly=True)

    street_to_merge_city_id = fields.Many2one(
        string="Street to merge city",
        related='street_to_merge_id.city_id',
        readonly=True,
    )
    use_city_id = fields.Boolean(string="Use city", default=True, )

    street_to_merge_code = fields.Char(string="Street to merge code", related='street_to_merge_id.code', readonly=True)
    use_code = fields.Boolean(string="Use code", default=False)

    similar_street_ids = fields.Many2many(
        string="Similar cities",
        comodel_name='res.street',
        compute='_get_similar_streets',
    )
    street_merge_destination_id = fields.Many2one(
        string="Merge destination",
        comodel_name='res.street',
        domain="[('id', 'in', similar_street_ids and similar_street_ids[0][2] or []), ('state', '=', 'confirmed')]",
    )
    number_partner_with_street_id = fields.Integer(
        string="Partners referencing this street :",
        compute='_compute_number_partner_with_street_id',
    )
    similarity_threshold = fields.Selection(
        string="Similarity",
        default='3',
        selection=[('1', 'Low'), ('3', 'Normal'), ('4', 'High'), ('6', 'Highest')],
    )

    new_name = fields.Char(
        string="Name",
        compute='_get_default_street_information',
        store=True,
        readonly=False,
    )
    new_code = fields.Char(
        string="Code",
        size=64,
        store=True,
        readonly=False,
        compute='_get_default_street_information',
        help="The official code for the street")
    new_city_id = fields.Many2many(
        string="City",
        comodel_name='res.city',
        store=True,
        readonly=False,
        compute='_get_default_street_information',
        domain="[('country_state_id', '=?', new_country_state_id)]",
    )
    new_country_state_id = fields.Many2one(
        string="State",
        comodel_name='res.country.state',
        store=True,
        readonly=False,
        compute='_get_default_street_information',
        domain="[('country_id', '=?', new_country_id)]",
    )
    new_country_id = fields.Many2one(
        string="Country",
        store=True,
        readonly=False,
        compute='_get_default_street_information',
        comodel_name='res.country',
    )

    destination_code = fields.Char(string="Code", readonly=True, related='street_merge_destination_id.code')
    destination_city_id = fields.Many2one(string="City", readonly=True, related='street_merge_destination_id.city_id')
    destination_country_id = fields.Many2one(
        string="Country",
        readonly=True,
        related='street_merge_destination_id.city_id.country_id',
    )
    destination_country_state_id = fields.Many2one(
        string="State",
        readonly=True,
        related='street_merge_destination_id.city_id.country_state_id',
    )
    destination_street_number = fields.Many2one(
        string="Overwrite street number",
        comodel_name='res.street.number',
    )
    new_street_number = fields.Many2one(
        string="Overwrite street number",
        comodel_name='res.street.number',
    )

    # endregion

    # region Fields method
    @api.depends('street_to_merge_id')
    def _compute_number_partner_with_street_id(self):
        """Count the number of partner referencing the street to merge."""
        self.number_partner_with_street_id = self.env['res.partner'].search_count(
            [('street_id', '=', self.street_to_merge_id.id)])

    @api.depends('street_to_merge_id')
    def _compute_street_renamed(self):
        """Initialize the street name used to search similar cities."""
        self.street_renamed = self.street_to_merge_id.name

    @api.depends('street_to_merge_id')
    def _get_default_street_information(self):
        """Initialize the street to merge information fields."""
        self.new_name = self.street_to_merge_id.name.upper()
        self.new_code = self.street_to_merge_id.code
        self.new_city_id = self.street_to_merge_id.city_id
        self.new_country_state_id = self.street_to_merge_id.city_id and self.street_to_merge_id.city_id.country_state_id
        self.new_country_id = self.street_to_merge_id.city_id and self.street_to_merge_id.city_id.country_id

    @api.depends('street_to_merge_id', 'street_renamed', 'use_city_id', 'use_name', 'use_code', 'similarity_threshold')
    def _get_similar_streets(self):
        """Search method used to find cities based on a "fuzzy" name."""
        search_domain = [('id', '!=', self.street_to_merge_id.id)]
        if not self.street_renamed:
            return None
        else:
            search_domain.append(('name', '%', self.street_renamed))
        if self.street_to_merge_city_id:
            search_domain.append(('city_id', '=', self.street_to_merge_city_id.id))
        if self.use_code and self.street_to_merge_code:
            search_domain.append(('code', '=', self.street_to_merge_code))

        if self.similarity_threshold != '3':
            # 0.3 is the default PSQL limit, it seems to be reset at each transaction
            # https://www.postgresql.org/docs/current/pgtrgm.html
            self.env.cr.execute('SELECT set_limit({limit:0.1f})'.format(limit=float(self.similarity_threshold) / 10))
        self.similar_street_ids = self.similar_street_ids.search(search_domain)

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_merge_street(self):
        u"""
        Fusion de ville.

        La rue source est supprimé au profit de la rue de destination, en tenant compte
        des éventuel partenaires possédant l'addresse qui va être fusionnée.
        """
        self.ensure_one()
        if not self.street_merge_destination_id:
            raise exceptions.ValidationError(_("Missing street, the merge need a destination"))

        referencing_street_rec = self.env['res.street'].search([('id', '=', self.street_to_merge_id.id)])
        # dé-référencement des rue de la ville à fusionner
        if referencing_street_rec:
            referencing_street_rec.write({'street_id': self.street_merge_destination_id.id})

        referencing_partner_rec = self.env['res.partner'].search([('street_id', '=', self.street_to_merge_id.id)])
        # On ne cherche que sur les partenaire, d'autres modèles peuvent référencer une rue, mais 'devrait'
        # ne référencer que les addresses référentielles, 'better_address' ne peux dépendre des autres modules
        if referencing_partner_rec:
            # Modification des addresses de partenaire basé sur la ville à supprimer (fusionner)
            new_address = {'street_id': self.street_merge_destination_id.id}
            if self.street_merge_destination_id.city_id:
                new_address['city_id'] = self.street_merge_destination_id.city_id.id
                if self.street_merge_destination_id.city_id.country_id:
                    new_address['country_id'] = self.street_merge_destination_id.city_id.country_id.id
                if self.street_merge_destination_id.city_id.country_state_id:
                    new_address['state_id'] = self.street_merge_destination_id.city_id.country_state_id.id
            if self.destination_street_number:
                new_address['street_number_id'] = self.destination_street_number.id

            # Modification des adresses existante
            referencing_partner_rec.write(new_address)

            if self.street_merge_destination_id.city_id:
                new_city = self.street_merge_destination_id.city_id
                for partner in referencing_partner_rec:
                    if not partner.zip_id and new_city.zip_ids:
                        # Si pas de code postal, on ajoute celui de la ville
                        partner.zip_id = new_city.zip_ids[0].id
                    elif partner.zip_id and not new_city.zip_ids:
                        # Si la ville n'a pas de code postal, on enlève celui du partner
                        partner.zip_id = None
                    elif partner.zip_id and new_city.zip_ids:
                        if partner.zip_id not in new_city.zip_ids:
                            # Si le code postal du partenaire ne fait pas parti de ceux de la ville, on le remplace
                            partner.zip_id = new_city.zip_ids[0].id

        self.street_to_merge_id.unlink()

        return self._open_street_view_form(self.street_merge_destination_id, target='current')

    @api.multi
    def action_add_street_to_referential(self):
        u"""
        Ajout de la rue à fusionner au référentiel.

        Dans le cas ou la rue n'est effectivement pas un doublon, les info requises sont renseignées afin d'ajouter
        la rue au référentiel.
        """
        self.ensure_one()
        if not self.new_city_id:
            raise exceptions.ValidationError(_("A city is required"))
        if not self.new_name:
            raise exceptions.ValidationError(_("A name is required"))

        if self.new_street_number:
            referencing_partner_rec = self.env['res.partner'].search([('street_id', '=', self.street_to_merge_id.id)])
            if referencing_partner_rec:
                referencing_partner_rec.write({'street_number_id': self.new_street_number.id})

        self.street_to_merge_id.write({
            'name': self.new_name,
            'state': 'confirmed',
            'code': self.new_code,
            'city_id': self.new_city_id.id,
        })

        return self._open_street_view_form(self.street_to_merge_id, target='main')

    @api.multi
    def action_open_google_map(self):
        """Open a new tab, on a Google map search."""
        related_city = self.street_to_merge_city_id
        query_string = '{city_name} {city_zip} {street_name}'.format(
            city_name=related_city and related_city.name or '',
            city_zip=related_city and related_city.zip_ids and related_city.zip_ids[0].name or '',
            street_name=self.street_to_merge_id and self.street_to_merge_id.name or '',
        )

        return {
            'type': 'ir.actions.act_url',
            'url': 'https://www.google.com/maps/place/' + quote_plus(query_string),
            'target': 'new',
        }

    # endregion

    # region Model methods
    def _open_street_view_form(self, street, target='new'):
        """Action to open street form view."""
        return {
            'context': self.env.context,
            'res_model': street._name,
            'type': 'ir.actions.act_window',
            'res_id': street.id,
            'view_mode': 'form',
            'target': target,
        }

    # endregion

    pass
