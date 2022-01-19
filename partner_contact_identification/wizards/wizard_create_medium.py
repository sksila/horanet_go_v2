import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval


class CreateMedium(models.TransientModel):
    """Allow a user to read/write a medium."""

    _name = 'partner.contact.identification.wizard.create.medium'

    def _get_default_mapping(self):
        return safe_eval(self.env['ir.config_parameter'].get_param(
            'partner_contact_identification.default_mapping_id', 'False'
        ))

    mapping_id = fields.Many2one(
        string="Mapping",
        comodel_name='partner.contact.identification.mapping',
        default=lambda self: self._get_default_mapping(),
        domain="[('mapping', 'in', ['csn', 'h3'])]"
    )
    max_length = fields.Integer(related='mapping_id.max_length')
    mapping = fields.Selection(related='mapping_id.mapping')

    external_reference = fields.Char(string="External reference")

    csn_number = fields.Char(string="CSN Number")

    def action_enroll_medium(self):
        tag_model = self.env['partner.contact.identification.tag']
        reference_id = self.env.context.get('default_reference_id', False)
        model_name = self.env.context.get('model_name', 'res.partner')
        if reference_id and model_name:
            self.env[model_name].browse(reference_id).check_access_rule('write')

        if not self.csn_number or not re.match("^[A-Z0-9]{" + str(self.mapping_id.max_length) + "}", self.csn_number):
            raise ValidationError(_("Enter a valid CSN number"))

        for rec in self:
            tag_rec = tag_model.with_context(active_test=False).search([
                ('number', '=', rec.csn_number),
                ('mapping_id', '=', rec.mapping_id.id)
            ])

            if not tag_rec:
                tag = tag_model.create({
                    'number': rec.csn_number,
                    'mapping_id': rec.mapping_id.id,
                    'external_reference': rec.external_reference
                })

                self.create_assignation(tag.id, model_name, reference_id)
                self.create_medium(tag_ids=tag.ids, type_id=False)

                continue

            if tag_rec.is_assigned:
                raise ValidationError(_("This tag is already assigned."))
            elif tag_rec.is_lost:
                raise ValidationError(_("This medium was declared as lost and cannot be used anymore."))
            else:
                tag_rec.mapped('medium_id').active = True
                for tag in tag_rec.mapped('medium_id').tag_ids:
                    rec.create_assignation(tag.id, model_name, reference_id)
                    tag.write({
                        'active': True,
                        'external_reference': rec.external_reference
                    })

    def action_enroll_and_continue(self):
        """Enroll the medium en recall the wizard."""
        self.action_enroll_medium()
        view = self.env.ref('partner_contact_identification.wizard_create_medium_form')
        return {
            'name': 'User',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.contact.identification.wizard.create.medium',
            'type': 'ir.actions.act_window',
            'view_id': view.id,
            'target': 'new',
        }

    @api.model
    def get_or_create_tag(self, mapping_name, tag_number=False):
        """Create a tag with optional number and return it.

        :param mapping_name: name of mapping to search for
        :param tag_number: tag number to use to create the tag
        :return: serialisable tag record
        """
        mapping = self.env['partner.contact.identification.mapping'].search([
            ('mapping', '=', mapping_name),
        ], limit=1)

        tag_obj = self.env['partner.contact.identification.tag']
        values = {'mapping_id': mapping.id}

        tag = tag_obj.with_context(active_test=False).search([
            ('mapping_id', '=', values['mapping_id']),
            ('number', '=', tag_number)
        ])

        if tag_number:
            values['number'] = tag_number

        if not tag:
            tag = tag_obj.create(values)
        else:
            if not tag.active:
                raise ValidationError(_("This medium was declared as lost and cannot be used anymore."))

        return tag.read(['number'])

    @api.model
    def delete_tag(self, tag_id):
        """Remove a tag from database.

        :param tag_id: id of the tag record to delete
        """
        self.env['partner.contact.identification.tag'].search([('id', '=', tag_id)]).unlink()

    @api.model
    def is_tag_assigned(self, tag_number):
        """Return assignation for a particular tag number.

        :param tag_number: number of the tag to filter on
        :return: serialisable assignation record
        """
        return self.env['partner.contact.identification.assignation'].search_read([
            ('tag_id.number', '=', tag_number),
            '|',
            ('end_date', '>=', fields.Datetime.now()),
            ('end_date', '=', False)
        ])

    @api.model
    def create_medium(self, tag_ids, type_id=False):
        """Create a medium with some tags.

        :param tag_ids: list of tag's id to attach to the medium
        :param type_id: the record of the type
        """
        medium_type = type_id or self.env['partner.contact.identification.medium.type'].search([], limit=1)

        medium_model = self.env['partner.contact.identification.medium']
        medium = medium_model.with_context(active_test=False).search([('tag_ids', 'in', tag_ids)])

        if not medium:
            medium_model.create({
                'tag_ids': [(6, 0, tag_ids)],
                'type_id': medium_type.id
            })
        else:
            medium.active = True
            medium.tag_ids = [(6, 0, tag_ids)]
            medium.tag_ids.write({'active': True})

    @api.model
    def create_assignation(self, tag_id, model, record_id):
        """Create an assignation with a tag and a partner.

        :param tag_id: id of tag record to attach to the assignation
        :param model: string of the model of record to attach to the assignation
        :param record_id: id of record to attach to the assignation
        """
        assignation_obj = self.env['partner.contact.identification.assignation']

        assignation_obj.create({
            'start_date': fields.Datetime.now(),
            'tag_id': tag_id,
            'reference_id': '%s,%s' % (model, record_id),
        })
