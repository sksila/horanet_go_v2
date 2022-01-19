from datetime import datetime, date
import re
from odoo import _, api, fields, models, exceptions
from odoo.exceptions import ValidationError
from odoo.osv import expression


class Tag(models.Model):
    """A tag is a unique identifier used to authenticate a citizen against collectivity services."""

    # region Private attributes
    _name = 'partner.contact.identification.tag'

    # endregion

    # region Default methods
    def _default_number(self):
        """Return a unique generated number for the tag."""
        return self.env['ir.sequence'].next_by_code('partner.contact.identification.tag')

    # endregion

    # region Fields declaration
    number = fields.Char(string="Number", required=True, default=_default_number)
    mapping_id = fields.Many2one(
        string="Mapping",
        comodel_name='partner.contact.identification.mapping',
        required=True
    )
    medium_id = fields.Many2one(
        string="Medium",
        comodel_name='partner.contact.identification.medium'
    )
    is_lost = fields.Boolean(related='medium_id.is_lost')
    active = fields.Boolean(string="Active", default=True)
    deactivated_by = fields.Many2one(
        string="Deactivated by", comodel_name='res.users',
        related='medium_id.deactivated_by'
    )
    deactivated_on = fields.Datetime(string="Deactivated on", related='medium_id.deactivated_on')
    is_assigned = fields.Boolean(
        string="Is assigned",
        compute='_compute_is_assigned',
        search='_search_is_assigned'
    )

    assignation_ids = fields.One2many(
        string="Assignations",
        comodel_name='partner.contact.identification.assignation',
        inverse_name='tag_id'
    )
    partner_id = fields.Many2one(
        string="Allocated to",
        comodel_name='res.partner',
        compute='compute_partner_id',
        search='search_partner_id'
    )
    assignation_start_date = fields.Date(compute='_compute_assignation_start_date')

    medium_label = fields.Char(string="Medium", compute='_compute_medium_label')

    external_reference = fields.Char(string="External reference")

    # endregion

    # region Fields method
    @api.depends('assignation_ids')
    def compute_partner_id(self):
        """Get the partner, using the assignation active at the current time."""
        for tag in self:
            tag.partner_id = tag.get_tag_partner()

    @api.model
    def search_partner_id(self, operator, value, search_date=False):
        """Search partners.

        :param operator: the search operator
        :param value: Boolean False or True
        :param search_date: optional, the date at which the search must be performed
        :return: A search domain
        """
        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        search_date_time = search_date or self.env.context.get('force_time', fields.Datetime.now())
        if isinstance(search_date_time, (datetime, date)):
            search_date_time = fields.Datetime.to_string(search_date_time)
        elif isinstance(search_date_time, str):
            search_date_time = fields.Datetime.to_string(fields.Datetime.from_string(search_date_time))
        else:
            raise ValueError('search_date_utc must be an Odoo date (str) or date object')

        if not isinstance(value, int) and not isinstance(value, list):
            raise TypeError("Search partner on tags: Expected integer or list of integer, found {bad_type}".format(
                bad_type=str(type(value)))
            )

        if isinstance(value, int):
            value = [value]

        assignation_model = self.env['partner.contact.identification.assignation']
        assignation_active_domain = assignation_model.search_is_active('=', True, search_date_time)
        assignations = assignation_model.search([('partner_id', 'in', value)] + assignation_active_domain)

        domain = [('assignation_ids', 'in', assignations.ids)]

        if (value and operator == '!=') or (not value and operator == '='):
            domain.insert(0, expression.NOT_OPERATOR)

        return domain

    @api.depends('assignation_ids')
    def _compute_assignation_start_date(self):
        for tag in self:
            active_assignation = tag.assignation_ids.filtered('is_active')

            if len(active_assignation) > 1:
                raise exceptions.ValidationError(
                    _("Anomaly detected: multiple active assignations found for tag %s") % tag.number
                )

            if active_assignation.partner_id:
                tag.assignation_start_date = active_assignation.start_date

    @api.depends()
    def _compute_is_assigned(self):
        """Compute if a tag is assigned or not."""
        assignation_model = self.env['partner.contact.identification.assignation']

        for rec in self:
            rec.is_assigned = bool(assignation_model.search([
                ('tag_id', '=', rec.id),
                ('is_active', '=', True)
            ]))

    def _search_is_assigned(self, operator, value):
        """Search tags which have an active assignation."""
        if operator not in ['=', '!=']:
            raise NotImplementedError("Got operator '{operator}' (expected '=' or '!=')".format(operator=operator))

        domain = expression.normalize_domain([('assignation_ids.is_active', '!=', False)])

        # Inverse for negative domain
        if bool(operator in expression.NEGATIVE_TERM_OPERATORS) == bool(value):
            domain = [expression.NOT_OPERATOR] + domain

        return domain

    @api.depends()
    def _compute_medium_label(self):
        horanet_area = self.env.ref('partner_contact_identification.area_horanet')
        for rec in self.filtered('medium_id'):
            medium_type = rec.medium_id.type_id

            csn_tag = ''
            for tag in rec.medium_id.mapped('tag_ids'):
                if tag.mapping_id.area_id == horanet_area:
                    csn_tag = tag.number

            rec.medium_label = medium_type.name + ' ' + csn_tag

    # endregion

    # region Constrains and Onchange
    @api.multi
    @api.constrains('mapping_id')
    def _check_unique_by_mapping(self):
        """Check if the current tag is unique for a given mapping.

        :raise: odoo.exceptions.ValidationError if the tag number already
            exists for the same mapping
        :raise: odoo.exceptions.ValidationError if the tag number already
            exists for the same technology and type of CSN
        """
        for rec in self:
            nb_tags = self.search_count([
                ('number', '=', rec.number),
                ('mapping_id', '=', rec.mapping_id.id)
            ])

            if nb_tags > 1:
                raise ValidationError(_("The tag number should be unique by mapping."))

            if rec.mapping_id.mapping == 'csn':
                nb_tags = self.search_count([
                    ('number', '=', rec.number),
                    ('mapping_id.technology_id', '=', rec.mapping_id.technology_id.id),
                    ('mapping_id.mapping', '=', rec.mapping_id.mapping)
                ])

                if nb_tags > 1:
                    raise ValidationError(_("The CSN tag number should be unique by mapping technology."))

    @api.constrains('medium_id')
    def _check_medium_has_tags_assigned_to_same_record(self):
        """Tags set on the medium should be assigned to same record."""
        for rec in self.filtered('medium_id'):
            assignations = rec.assignation_ids.filtered(lambda a: not a.end_date)

            try:
                if len(assignations.mapped('reference_id')) > 1:
                    raise ValidationError(_("Tags on the same medium should be assigned to the same entity."))
            except TypeError:
                raise ValidationError(_("Tags on the same medium should be assigned to the same entity."))

    @api.constrains('number', 'mapping_id')
    def _check_tag_respect_mapping_config(self):
        """Check if the tag number respect the mapping regex."""
        if self.mapping_id and self.mapping_id.regex:
            if not re.match(self.mapping_id.regex, self.number):
                raise ValidationError(_("The number not match with the mapping regex."))

    @api.onchange('number', 'mapping_id')
    def _onchange_number_respect_mapping(self):
        """Format the tag number with the mapping parameters.

        Mapping define can define how we record the tag number (uppercase, lowercase,
        concatenation of capturing groups by the regex).
        """
        if self.mapping_id.tag_format_recording == 'upper':
            self.number = self.number.upper()
        elif self.mapping_id.tag_format_recording == 'lower':
            self.number = self.number.lower()

        if self.mapping_id and self.mapping_id.regex:
            regex_result_match = re.match(self.mapping_id.regex, self.number)
            result = ""
            if regex_result_match:
                groups = regex_result_match.groups()
                if groups:
                    for group in groups:
                        if group != self.number:
                            result += group
                else:
                    for match in re.findall(self.mapping_id.regex, self.number):
                        result += match

                if result != "":
                    self.number = result

    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        """Return the display name of the record."""
        result = []
        display_partner_in_tag_name = self.env.context.get('display_partner_in_tag_name', False)

        separator = ' - '
        for rec in self:
            name = ' --- '
            if display_partner_in_tag_name:
                partner_name = rec.partner_id.name if rec.partner_id else None
                name = "N° {tag_number}{separator}{partner_name}".format(
                    tag_number=rec.number,
                    separator=separator if partner_name else '',
                    partner_name=partner_name or '')
            else:
                name = "N° {tag_number}{separator}{mapping}".format(
                    tag_number=rec.number,
                    separator=separator,
                    mapping=rec.mapping_id.display_name)
            result.append((rec.id, name))

        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to search street number that 'start with'."""
        if args is None:
            args = []
        res = []

        ids = self.search([('number', '=ilike', str(name) + '%')] + args, limit=limit).ids
        for rec in self.browse(ids):
            res.append((rec.id, rec.display_name))
        return res

    @api.model
    def create(self, vals):
        """Create a Tag with mapping rules."""
        if 'mapping_id' in vals.keys() and 'number' in vals.keys():
            mapping_rec = self.env['partner.contact.identification.mapping'].browse(vals['mapping_id'])
            if mapping_rec.tag_format_recording == 'upper':
                vals['number'] = vals['number'].upper()
            elif mapping_rec.tag_format_recording == 'lower':
                vals['number'] = vals['number'].lower()

            if mapping_rec.regex:
                regex_result_match = re.match(mapping_rec.regex, vals['number'])
                result = ""
                if not regex_result_match:
                    raise ValidationError(_("The number not match with the mapping regex."))
                else:
                    groups = regex_result_match.groups()
                    if groups:
                        for group in groups:
                            if group != vals['number']:
                                result += group
                    else:
                        for match in re.findall(mapping_rec.regex, vals['number']):
                            result += match

                    vals['number'] = result if result != "" else vals['number']

        new_tag = super(Tag, self).create(vals)
        return new_tag

    # endregion

    # region Actions
    @api.multi
    def deallocate(self):
        """Deallocate all the tags that are presents on the tag's medium. Tags remain active."""
        if self.mapped('medium_id'):
            self.mapped('medium_id').deallocate()
        else:
            self.assignation_ids.filtered(lambda a: not a.end_date).end_assignation()

    @api.multi
    def set_lost(self):
        """Deactivate a tag's medium, its tags and their assignations."""
        self.mapped('medium_id').set_lost()

    @api.multi
    def deactivate(self):
        """Deactivate the current tag and its assignation."""
        self.write({'active': False})
        self.assignation_ids.filtered(lambda a: not a.end_date).end_assignation()

    # endregion

    # region Model methods
    @api.multi
    def get_tag_partner(self, search_date_utc=None):
        """Return if it exists, the partner at the specified date.

        :param search_date_utc: the date used to search the partner via the assignations (in UTC)
        :return: None or a partner (record)
        """
        self.ensure_one()
        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        search_date_time = search_date_utc or self.env.context.get('force_time', datetime.now())
        result = self.env['res.partner']

        if isinstance(search_date_time, (datetime, date)):
            search_date_time = fields.Datetime.to_string(search_date_time)
        elif isinstance(search_date_time, str):
            search_date_time = fields.Datetime.to_string(fields.Datetime.from_string(search_date_time))
        else:
            raise ValueError('search_date_utc must be an Odoo date (str) or date object')

        assignation_model = self.env['partner.contact.identification.assignation']
        search_active_domain = assignation_model.search_is_active('=', 'active', search_date=search_date_time)

        assignations = assignation_model.search(
            ['&', ('reference_id', '!=', False), ('tag_id', '=', self.id)] + search_active_domain)

        for assignation in assignations:
            if assignation.partner_id:
                result += assignation.partner_id

        # Trick to remove duplicates
        result = result & result

        return result

    @api.multi
    def get_partner_linked_to_tag(self, search_date_utc=None):
        """Return if it exists, the partner linked to the tag.

        doesn't matter if he is assigned to a move, a package or a partner.
        This method can be override to give the partner if the assignation point to a object other than a partner.

        :param search_date_utc: the date used to search the partner via the assignations (in UTC)
        :return: None or a partner (record)
        """
        self.ensure_one()
        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        search_date_time = search_date_utc or self.env.context.get('force_time', datetime.now())

        if isinstance(search_date_time, (datetime, date)):
            search_date_time = fields.Datetime.to_string(search_date_time)
        elif isinstance(search_date_time, str):
            search_date_time = fields.Datetime.to_string(fields.Datetime.from_string(search_date_time))
        else:
            raise ValueError('search_date_utc must be an Odoo date (str) or date object')

        assignation_model = self.env['partner.contact.identification.assignation']
        search_active_domain = assignation_model.search_is_active('=', 'active', search_date=search_date_time)

        assignations = assignation_model.search(
            ['&', ('reference_id', '!=', False), ('tag_id', 'in', self.ids)] + search_active_domain)

        result = assignations.get_partner_linked_to_assignation()

        return result

    @api.multi
    def get_partner_linked_to_multiple_tag(self, start_date, end_date):
        u"""Return if it exists, information to find the partner linked to the tag.

        doesn't matter if he is assigned to a move, a package or a partner.
        This method can be override to give the partner if the assignation point to a object other than a partner.

        L'astuce est de de considérer qu'il y a peu d'assignations par tag, et donc d'éviter de faire une recherche
        en base par tag, au profit d'une seul recherche des assignations des tag, puis de réaliser en python
        la recherche des assignations actives (voir champ operation_partner_id du model operation)

        Attention: Cette méthode est appelée sur un recordset, elle renvoie un dictionnaire d'association
        de {tag_rec: [(date_start, date_end, partner_rec]}, cela permet de gagner en performance lors du calcul
        en masse, car la recherche de la bonne assignation peut se faire en python.

        :param str/datetime start_date: lower date range to research assignation object (in UTC)
        :param str/datetime end_date: upper date range to research assignation object (in UTC)
        :return: dictionary <tag:(assignation_start_date, assignation_end_date, partner)>
        """
        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        if self.env.context.get('force_time', False):
            start_date = end_date = self.env.context['force_time']

        if isinstance(start_date, (datetime, date)):
            start_date_time = fields.Datetime.to_string(start_date)
        elif isinstance(start_date, str):
            start_date_time = fields.Datetime.to_string(fields.Datetime.from_string(start_date))
        else:
            raise ValueError("start_date must be an Odoo date (str) or date object")
        if isinstance(end_date, (datetime, date)):
            end_date_time = fields.Datetime.to_string(end_date)
        elif isinstance(end_date, str):
            end_date_time = fields.Datetime.to_string(fields.Datetime.from_string(end_date))
        else:
            raise ValueError("start_date must be an Odoo date (str) or date object")

        assignations = self.env['partner.contact.identification.assignation'].search([
            ('reference_id', '!=', False),
            ('tag_id', 'in', self.ids),
            '!',
            '&',
            ('start_date', '>', end_date_time),
            '|',
            ('end_date', '!=', False),
            ('end_date', '<', start_date_time)
        ])

        result = assignations.get_partner_linked_to_multiple_assignation()

        return result

    # endregion

    pass
