# coding: utf-8

import base64

from odoo import api, fields, exceptions, models, _


class CardMakerExport(models.Model):
    _name = 'partner.contact.identification.cardmaker.export'

    name = fields.Char()
    create_uid = fields.Many2one(
        string="Created by",
        comodel_name='res.users',
        readonly=True
    )
    create_date = fields.Datetime(readonly=True)

    category_id = fields.Many2one(
        string="Partners category",
        comodel_name='subscription.category.partner',
        readonly=True
    )

    partner_ids = fields.Many2many(
        string="Partners",
        comodel_name='res.partner',
        readonly=True
    )
    nb_partners = fields.Integer(
        string="Number of partners",
        compute='_compute_nb_partners'
    )

    generated_filename = fields.Char()
    generated_file = fields.Binary(readonly=True)
    imported_filename = fields.Char()
    imported_file = fields.Binary()

    do_files_match = fields.Boolean(
        compute='_compute_do_files_match',
        store=True
    )
    import_date = fields.Datetime(readonly=True)

    @api.depends('partner_ids')
    def _compute_nb_partners(self):
        """Compute the number of partners."""
        for rec in self:
            rec.nb_partners = len(rec.partner_ids)

    @api.depends('generated_file', 'imported_file')
    def _compute_do_files_match(self):
        """Check if generated_file and imported_file match."""
        for rec in self:
            if not rec.imported_file:
                rec.do_files_match = False
                continue

            # onchange call pass NewId and size of generated file instead of its content
            # as it's a NewId, we cannot search in the database to look for real
            # content so skip the onchange check
            if isinstance(rec.id, models.NewId):
                continue

            generated_file = base64.b64decode(rec.generated_file.decode('utf-8-sig'))
            imported_file = base64.b64decode(rec.imported_file.decode('utf-8-sig'))

            rec.do_files_match, msg = self.files_match(generated_file, imported_file)

            if not rec.do_files_match:
                raise exceptions.ValidationError(msg)

    def files_match(self, first_file, second_file):
        """Compare two CSV filelike (string) and check if they match.

        :param first_file: string CSV file generated from the wizard
        :param second_file: string CSV file retrieved from cardmaker
        :return: boolean, string with meaningful message
        """
        first_file_lines = first_file.split('\n')
        second_file_lines = second_file.split('\n')

        # We don't care about the head line
        if '"ID"' in first_file_lines[0]:
            del first_file_lines[0]
        if '"ID"' in second_file_lines[0]:
            del second_file_lines[0]

        # Those are empty so delete them
        del first_file_lines[-1]
        del second_file_lines[-1]

        if len(first_file_lines) != len(second_file_lines):
            return False, _("The number of lines don't match")

        serial_numbers = []
        for i in xrange(len(first_file_lines)):
            # We don't want to compare last two columns as they should be different
            if first_file_lines[i].split('";"')[0:11] != second_file_lines[i].split('";"')[0:11]:
                return False, _("Files don't match on line %s.") % str(i + 1)

            if not second_file_lines[i].split('";"')[12].replace('"', ''):
                return False, _("CSN column not filled on line %s.") % str(i + 1)

            # Check if there are duplicate CSN
            csn = second_file_lines[i].split('";"')[12].replace('"', '')
            if csn in serial_numbers:
                return False, _('Duplicated CSN number found "%s".') % csn

            serial_numbers.append(csn)

        return True, ''

    @api.multi
    def create_mediums_and_tags(self):
        self.ensure_one()

        imported_file_lines = base64.b64decode(self.imported_file).split('\n')

        # We don't care about the head line
        if '"ID"' in imported_file_lines[0]:
            del imported_file_lines[0]

        for line in imported_file_lines:
            columns = line.replace('\r', '') \
                          .replace('\n', '') \
                          .replace('"', '') \
                          .split(';')

            if not columns[0]:
                continue

            assignation = self.env['partner.contact.identification.assignation'].search([
                ('partner_id', '=', int(columns[0])),
                ('tag_id.mapping_id.id', '=', columns[10]),
                ('tag_id.number', '=', columns[12]),
                ('end_date', '=', False)
            ])

            # We don't want to do anything if there is already a tag with this csn
            # assigned to that partner
            if assignation:
                continue

            self.create_assignations(
                int(columns[0]),
                {
                    'mapping_id': columns[10],
                    'csn_number': columns[12]
                }
            )
            self.env.cr.commit()
            self.env.clear()

        self.import_date = fields.Datetime.now()

    def create_assignations(self, partner_id, values):
        self.env['partner.contact.identification.wizard.create.medium'] \
            .with_context({'default_reference_id': partner_id}) \
            .create(values).action_enroll_medium()
