from collections import defaultdict
from datetime import datetime, date

from odoo import _, api, exceptions, fields, models
from odoo.osv import expression
from odoo.exceptions import ValidationError


class Assignation(models.Model):
    """Assign a tag to a partner for some duration."""

    # region Private attributes
    _name = 'partner.contact.identification.assignation'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    start_date = fields.Datetime(
        string="Start date",
        default=fields.Datetime.now,
        required=True,
        store=True,
    )
    end_date = fields.Datetime(
        string="End date",
        store=True,
    )
    is_active = fields.Boolean(
        string="Is active",
        compute='compute_is_active',
        search='search_is_active',
        store=False,
    )
    tag_id = fields.Many2one(
        string="Tag",
        comodel_name='partner.contact.identification.tag',
        required=True,
        auto_join=True,
    )
    external_reference = fields.Char(related='tag_id.external_reference')
    medium_label = fields.Char(related='tag_id.medium_label')

    reference_id = fields.Reference(string="Assigned to", selection=[('res.partner', "User")], oldname='partner_id')

    partner_id = fields.Many2one(
        string="Partner",
        comodel_name='res.partner',
        compute='_compute_partner_id',
        ondelete='restrict',
        index=True,
        store=True,
        auto_join=True,
    )
    display_type_assignation = fields.Char(
        string="Type assignation",
        compute='compute_display_type_assignation',
        store=False,
    )

    display_name_assignation = fields.Char(
        string="Assigned to",
        compute='compute_display_name_assignation',
        store=False,
    )

    # endregion

    # region Fields method
    @api.constrains('tag_id')
    def _check_if_tag_is_available(self):
        """Check if current `tag_id` is already assigned.

        :raises: exceptions.ValidationError if tag is assigned
        """
        for rec in self:
            if rec.tag_id and rec.tag_id.is_assigned:
                assignations = self.search([
                    ('id', '!=', rec.id),
                    ('tag_id', '=', rec.tag_id.id),
                    ('end_date', '=', False),
                    ('start_date', '<=', rec.end_date)
                ])

                if assignations:
                    raise exceptions.ValidationError(
                        _("This tag is already assigned.")
                    )

    @api.depends('reference_id')
    def _compute_partner_id(self):
        """Ajout d'un champ stocké afin de faciliter les recherches sur les assignation de partner."""
        for assignation in self:
            if assignation.reference_id and assignation.reference_id._name == 'res.partner':
                assignation.partner_id = assignation.reference_id
            else:
                assignation.partner_id = None

    @api.depends('reference_id')
    def compute_display_type_assignation(self):
        """Ajout d'un champ stocké afin de faciliter les recherches sur les assignation de partner."""
        dict_selection_reference = dict(self.fields_get('reference_id', 'selection')['reference_id']['selection'])
        for assignation in self:
            if assignation.reference_id:
                assignation.display_type_assignation = dict_selection_reference.get(assignation.reference_id._name, '')
            else:
                assignation.display_type_assignation = False

    @api.depends('start_date', 'end_date')
    def compute_is_active(self):
        """Compute the active property of the assignation at the current date."""
        search_date = fields.Datetime.now()

        for assignation in self:
            if assignation.end_date:
                assignation.is_active = assignation.start_date <= search_date < assignation.end_date
            else:
                assignation.is_active = assignation.start_date <= search_date

    @api.depends('partner_id')
    def compute_display_name_assignation(self):
        u"""Calcul le nom des assignations liée a un partenaire (res.partner).

        Une assignation peut être liée à plusieurs objets via un champ reference.
        Pour des raisons de performance, le nom de l'assignation est calculé à partir de l'objet référencé et non
        depuis le champ référence.

        Plusieurs méthodes surchargent le calcul du nom de l'assignation, chacune traitant un type d'objet.
        """
        for assignation in self:
            if assignation.partner_id:
                assignation.display_name_assignation = assignation.partner_id.name
            else:
                assignation.display_name_assignation = "---"

    def search_is_active(self, operator, value, search_date=False):
        """Determine the domain used to search assignation by is_active value.

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

        domain = [
            '&',
            ('start_date', '<=', search_date_time),
            '|',
            ('end_date', '=', False), ('end_date', '>=', search_date_time)
        ]

        if (value and operator == '!=') or (not value and operator == '='):
            domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(domain)

    # endregion

    # region Constrains and Onchange
    @api.constrains('start_date', 'end_date')
    def _check_date_consistency(self):
        for rec in self:
            if not rec.end_date:
                continue

            if rec.end_date < rec.start_date:
                raise ValidationError(_("End date should be posterior or equal to start date."))

    @api.constrains('tag_id', 'start_date', 'end_date')
    def _check_unicity(self):
        """Ajout d'une contrainte de vérification de duplicité d'assignation.

        Permet d'éviter d'avoir deux assignations sur la même période
        """
        for assignation in self:
            duplicity_domain = [
                ('id', '!=', assignation.id),
                ('tag_id', '=', assignation.tag_id.id)]

            if not assignation.end_date:
                duplicity_domain.extend([
                    '|',
                    ('end_date', '=', False),
                    ('end_date', '>', assignation.start_date),
                ])

            else:
                duplicity_domain.extend([
                    '|',
                    '&',
                    ('end_date', '=', False),
                    ('start_date', '<', assignation.end_date),
                    '&',
                    ('start_date', '<', assignation.end_date),
                    ('end_date', '>', assignation.start_date)
                ])

            duplicates = self.search(duplicity_domain)

            # Si doublon's trouvés retourner une exception ORM
            if duplicates:
                raise exceptions.ValidationError(_(
                    "Duplicate assignation ({duplicate_ids}) found for the tag id {tag_id}"
                    " for the period {period}.".format(
                        duplicate_ids=str(','.join([str(dup_id) for dup_id in duplicates.ids])),
                        tag_id=str(assignation.tag_id.id),
                        period="{start_date} <--> {end_date}".format(
                            start_date=str(assignation.start_date),
                            end_date=str(assignation.end_date) if assignation.end_date else '...'
                        )
                    )
                ))

    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        """Surcharge de la méthode de base.

        Returns a textual representation for the records in ``self``.
        By default this is the value of the ``display_name`` field.

        :return: list of pairs ``(id, text_repr)`` for each records
        :rtype: list(tuple)
        """
        return [(assignation.id, "{} - {}".format(
            assignation.reference_id.name_get()[0][1] if assignation.reference_id else '',
            assignation.tag_id.number))
                for assignation in self]

    @api.model
    def create_assignations(self, tag_ids, model, record_id, start_date=False, end_date=False):
        """Create an assignation between tags and a model (partner, move, subscription).

        :param tag_ids: recordset of tags
        :param model: string of the model of record to attach to the assignation
        :param record_id: record to attach to the assignation
        :param start_date: start date of the assignation, by default the date of today
        :param end_date: end date of the assignation (optional)
        """
        date = start_date if start_date else fields.Datetime.now()
        end_date = end_date if end_date else False

        new_assignations = self.env['partner.contact.identification.assignation']
        for tag_id in tag_ids:
            if not tag_id.is_assigned:
                new_assignations += self.create({
                    'start_date': date,
                    'end_date': end_date,
                    'tag_id': tag_id.id,
                    'reference_id': '{ref_model},{rec_id}'.format(ref_model=model, rec_id=record_id.id),
                })
        return new_assignations

    # endregion

    # region Actions
    @api.multi
    def end_assignation(self):
        """Set the end date of assignation to the current date."""
        related_partner_ids = self.mapped('partner_id')
        if related_partner_ids:
            related_partner_ids.check_access_rule('write')

        self.write({'end_date': fields.Datetime.now()})

    @api.multi
    def deallocate(self):
        """Deallocate all the linked tags. Tags remain active."""
        self.mapped('tag_id').deallocate()

    @api.multi
    def set_lost(self):
        self.mapped('tag_id').set_lost()

    # endregion

    # region Model methods
    @api.multi
    def get_partner_linked_to_assignation(self):
        """Return if it exists, the partner linked to the assignation.

        doesn't matter if the assignation is linked to a move, a package or a partner.
        This method can be override to give the partner if the assignation point to a object other than a partner.

        :return: None or a partner (record)
        """
        result = self.env['res.partner']
        for assignation in self.filtered('partner_id'):
            result += assignation.partner_id

        # Trick to remove duplicates
        result = result & result

        return result

    @api.multi
    def get_partner_linked_to_multiple_assignation(self):
        """Return if it exists, the partner linked to the assignation.

        doesn't matter if the assignation is linked to a move, a package or a partner.
        This method can be override to give the partner if the assignation point to a object other than a partner.

        :return: dictionary <tag:(assignation_start_date, assignation_end_date, partner)>
        """
        result = defaultdict(list)
        for ass in self.filtered('partner_id'):
            result[ass.tag_id].append((ass.start_date, ass.end_date, ass.partner_id))

        return result

    # endregion

    pass
