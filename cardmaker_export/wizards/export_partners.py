# coding: utf-8

import base64
import os
import codecs

from odoo import api, fields, models, _
from odoo.addons.mail.models.mail_template import format_tz


class PartnerExportWizard(models.TransientModel):
    """Create `cardmaker.export` record.

    This class is only used to be able to filter on partners that don't have
    an active medium and export those.

    The export has a CSV file containing required information that is sent to
    our cardmaker partner that will be able to make cards for the partners and
    send back to us the modified file with serial numbers assigned to each partners.
    """

    _name = 'partner.contact.identification.cardmaker.export.wizard'

    category_id = fields.Many2one(
        string="Partners category",
        comodel_name='subscription.category.partner',
        required=True
    )
    mapping_id = fields.Many2one(
        string="Mapping",
        comodel_name='partner.contact.identification.mapping',
        required=True
    )
    partner_ids = fields.Many2many(
        string="Partners",
        comodel_name='res.partner',
        compute='_compute_partner_ids',
        required=True
    )
    invalid_partner_ids = fields.Many2many(
        string="Invalid partners",
        comodel_name='res.partner',
        compute='_compute_partner_ids',
        help=("Partners in this list won't be exported because they have missing "
              "informations (address or title fields)")
    )

    @api.depends('category_id')
    def _compute_partner_ids(self):
        """Return partners that match category and don't have an active medium."""
        self.ensure_one()

        partners = self.env['res.partner'].search([
            ('subscription_category_ids', 'in', self.category_id.ids),
            ('has_active_medium', '!=', True),  # This could be deleted if part of the category
            ('id', '!=', 3)  # We don't want to export the admin partner
        ])

        exported_partners = self.env['partner.contact.identification.cardmaker.export'].search([
            ('import_date', '=', False)
        ]).mapped('partner_ids')

        unexported_partners = partners - exported_partners

        self.partner_ids = unexported_partners.filtered('street_number_id') \
                                              .filtered('street_id') \
                                              .filtered('zip_id') \
                                              .filtered('city_id')
        self.invalid_partner_ids = unexported_partners - self.partner_ids

    @api.multi
    def action_export(self):
        """Create a record of `partner.contact.identification.cardmaker.export`.

        This method generate a CSV file and attach it to the record.
        """
        self.ensure_one()

        date = format_tz(self.env, self.create_date)
        name = '%s %s' % (date, self.category_id.name)

        head_line = _('"ID";"TITLE";"FIRSTNAME";"LASTNAME";"STREET1";"STREET2";"ZIP";"CITY";"STATE";"COUNTRY";"MAPPING";"NUMBER";"UID"') + '\n' # noqa

        partners = self.generate_partners_list()

        lines = ('"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s"\n' % (
            partner.id,
            partner.title.shortcut.strip().replace('"', '') if partner.title else '',
            partner.firstname.strip().replace('"', '') if partner.firstname else '',
            partner.lastname.strip().replace('"', ''),
            partner.street_number_id.name.strip().replace('"', '') + ' ' + partner.street_id.name.strip().replace('"', ''), # noqa
            partner.street2.strip().replace('"', '') if partner.street2 else '',
            partner.zip_id.name.strip().replace('"', ''),
            partner.city_id.name.strip().replace('"', ''),
            '',  # TODO: Use this when we'll export card for foreign countries
            partner.country_id.name.strip().replace('"', '') if partner.country_id else '',
            self.mapping_id.id,
            '', ''  # Last two columns are filled by the cardmaker
        ) for partner in partners)

        with codecs.open('/tmp/export.txt', mode='w', encoding='utf-8-sig') as f:
            f.write(head_line)
            f.write(''.join(lines))

        with codecs.open('/tmp/export.txt', mode='r', encoding='utf-8-sig') as f:
            export = self.env['partner.contact.identification.cardmaker.export'].create({
                'name': name,
                'category_id': self.category_id.id,
                'partner_ids': [(4, self.partner_ids.ids)],
                'generated_file': base64.b64encode(f.read().encode('utf-8-sig')),
                'generated_filename': name + '.txt'
            })

        os.remove('/tmp/export.txt')

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'partner.contact.identification.cardmaker.export',
            'res_id': export.id,
            'view_mode': 'form'
        }

    def generate_partners_list(self):
        return [p for p in self.partner_ids.sorted(lambda p: p.city_id.name)]
