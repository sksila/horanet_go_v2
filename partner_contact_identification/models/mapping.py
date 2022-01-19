import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Mapping(models.Model):
    """A mapping represents the architecture: technology and area of a medium."""

    # region Private attributes
    _name = 'partner.contact.identification.mapping'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    technology_id = fields.Many2one(
        string="Technology",
        comodel_name='partner.contact.identification.technology',
        required=True
    )
    area_id = fields.Many2one(
        string="Area",
        comodel_name='partner.contact.identification.area',
        required=True
    )
    mapping = fields.Selection(
        string="Type",
        selection=[('csn', "CSN"),
                   ('h3', "H3"),
                   ('ean13', "EAN 13")],
        required=True
    )
    max_length = fields.Integer(
        string="Max length",
        help="Value used when creating a tag to prevent its value to be too long",
    )

    tag_format_recording = fields.Selection(
        string="Action before recording",
        selection=[('nothing', 'Nothing'), ('upper', 'Upper'), ('lower', 'Lower')],
        default='nothing',
        help="This format is used before recording or match with the regex",
    )

    regex = fields.Char(
        string="Regex",
        help="This regex is used to validate and save a tag. "
             "If regex has multiple groups when match, we record the sum of groups (which are different that the "
             "initial data). Exemple: for the data 'AA-123-BB', if the match has "
             "4 groups: 'AA-123-BB', 'AA', '123', 'BB'. We record: 'AA123BB'. "
             "You can use tools like regex101 to validate the regex and capturing groups. "
    )

    regex_test = fields.Char(
        string="Test of regex",
        store=False,
    )

    regex_result = fields.Boolean(
        string="Result of the regex test",
        store=False,
    )

    result_of_recording = fields.Char(
        string="Result of recording",
        store=False,
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.multi
    @api.constrains('technology_id', 'area_id', 'mapping')
    def _check_existing_record(self):
        """Check if a mapping with those properties already exists.

        :raise: odoo.exceptions.ValidationError if the same mapping already exists
        """
        for rec in self:
            mapping = rec.search([
                ('technology_id', '=', rec.technology_id.id),
                ('area_id', '=', rec.area_id.id),
                ('mapping', '=', rec.mapping),
                ('id', '!=', rec.id)
            ])

            if mapping:
                raise ValidationError(_("There is already an existing mapping with these properties."))

    @api.onchange('mapping')
    def _onchange_mapping(self):
        """Change `max_length` value based on `mapping`."""
        if self.mapping == 'csn':
            self.max_length = 8
        elif self.mapping == 'h3':
            self.max_length = 16
        elif self.mapping == 'ean13':
            self.max_length = 13

    @api.onchange('regex_test')
    def onchange_test_regex(self):
        """Calcul if the data in the regex_test match with the regex."""
        if self.tag_format_recording == 'upper':
            self.regex_test = self.regex_test.upper()
        elif self.tag_format_recording == 'lower':
            self.regex_test = self.regex_test.lower()

        if self.regex and self.regex_test:
            regex_result_match = re.match(self.regex, self.regex_test)
            result = ""
            if regex_result_match:
                self.regex_result = True
                groups = regex_result_match.groups()
                if groups:
                    for group in groups:
                        if group != self.regex_test:
                            result += group
                else:
                    for match in re.findall(self.regex, self.regex_test):
                        result += match
                self.result_of_recording = result if result != "" else self.regex_test
            else:
                self.regex_result = False
                self.result_of_recording = ""

    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        """Return the display name of the record."""
        result = []
        for rec in self:
            name = '{} {} {}'.format(
                rec.technology_id.display_name,
                rec.area_id.display_name,
                rec.mapping
            )
            result.append((rec.id, name))
        return result

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
