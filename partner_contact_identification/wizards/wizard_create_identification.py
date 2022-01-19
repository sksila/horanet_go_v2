# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, exceptions
from odoo.exceptions import ValidationError


class CreateIdentification(models.TransientModel):
    """Allow a user to read/write a medium."""

    # region Private attributes
    _name = 'create.identification'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    medium_selection = fields.Selection(
        string="Medium selection",
        selection=[('create', "Create new medium"), ('update', "Update medium")],
        default='create',
    )

    tag_ids = fields.Many2many(
        string="Tags",
        comodel_name='partner.contact.identification.tag',
    )

    assignation_ids = fields.Many2many(
        string="Assignations",
        comodel_name='partner.contact.identification.assignation',
        compute='_compute_assignation_ids',
    )

    medium_id = fields.Many2one(
        string="Medium",
        comodel_name='partner.contact.identification.medium',
    )

    tag_number = fields.Char(string="Number")
    mapping_id = fields.Many2one(
        string="Mapping",
        comodel_name='partner.contact.identification.mapping',
    )

    external_reference = fields.Char(string="External Reference")

    entity_to_assigned = fields.Selection(
        string="Entity to assigned",
        selection=[('res.partner', "Partner"),
                   ],
        default='res.partner',
    )

    partner_to_assign = fields.Many2one(
        string="Partner to assign",
        comodel_name='res.partner',
    )

    start_date = fields.Datetime(
        string="Start date",
        default=fields.Datetime.now,
        required=True,
    )

    end_date = fields.Datetime(string="End date")

    type_id = fields.Many2one(
        string="Medium type",
        comodel_name='partner.contact.identification.medium.type',
    )

    medium_tag_ids = fields.One2many(related='medium_id.tag_ids')

    create_or_select_tags = fields.Selection(
        string="Create or select tags",
        selection=[('create', "Create new tag"), ('select', "Select existing tags")],
        default='create',
    )

    show_assignation_button = fields.Boolean(
        string="Show assignation button",
        default=True,
    )
    # endregion

    # region Fields method
    @api.depends('partner_to_assign')
    def _compute_assignation_ids(self):
        """Compute assignation_ids."""
        for rec in self:
            rec.assignation_ids = self.env['partner.contact.identification.assignation'].search(
                [('partner_id', '=', rec.partner_to_assign.id)]).ids

    # endregion

    # region Constraints and Onchange
    @api.onchange('tag_ids')
    def _onchange_show_assignation_button(self):
        """Put show_assignation_button at true when we select a tag (to assigned a tag after creating one)."""
        self.show_assignation_button = True

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_create_tag(self):
        self.ensure_one()

        tag_number = self.tag_number
        tag_mapping_id = self.mapping_id
        tag_external_ref = self.external_reference

        if not tag_number or not tag_mapping_id:
            raise ValidationError(_("A tag must have a number and a mapping"))

        tag_rec = self.env['partner.contact.identification.tag'].with_context(active_test=False).search([
            ('number', '=', tag_number),
            ('mapping_id', '=', tag_mapping_id.id)
        ])

        if not tag_rec:
            tag = self.env['partner.contact.identification.tag'].create({
                'number': tag_number,
                'mapping_id': tag_mapping_id.id,
                'external_reference': tag_external_ref
            })
        else:
            raise ValidationError(_("The tag already exists"))

        self.tag_ids = [(4, tag.id)]
        self.action_create_assignation()
        self.create_or_select_tags = 'select'
        self.show_assignation_button = False

        return self._refresh_wizard()

    def action_create_assignation(self):
        self.ensure_one()

        if self.entity_to_assigned == 'res.partner':
            entity_id = self.partner_to_assign
        else:
            entity_id = False

        if entity_id:
            self.env['partner.contact.identification.assignation'].create_assignations(
                self.tag_ids, self.entity_to_assigned, entity_id, self.start_date, self.end_date)
        else:
            raise exceptions.UserError(_("A partner is required"))

        return self._refresh_wizard()

    def action_create_medium(self):
        self.ensure_one()

        self.env['partner.contact.identification.medium'].create_medium(tag_ids=self.tag_ids, type_id=self.type_id)
        return self._refresh_wizard()

    def action_update_medium(self):
        self.ensure_one()

        self.medium_id.tag_ids += self.tag_ids
        return self._refresh_wizard()

    # endregion

    # region Model methods
    @api.multi
    def _refresh_wizard(self):
        self.ensure_one()

        # Rappel du wizard en gardant son contexte
        return {
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # endregion
