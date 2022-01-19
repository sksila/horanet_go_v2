import ast
# 1 : imports of python lib
import logging
import re

# 2 :  imports of openerp
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

INFORMATION_TYPES = [
    ('number', "Number"),
    ('text', "Text"),
    ('option', "Choice"),
    ('selection', "Selection"),
    ('date', 'Date'),
    ('document', 'Document'),
    ('explanation', 'Explanation'),
    ('model', "Model"),
    ('hidden', "Hidden"),
]

INFORMATION_MODES = [
    ('query', "Query"),
    ('result', "Result")
]

INFORMATION_OPTION_VALUES = {0: _("No"), 1: _("Yes")}

TYPE2FIELD = {
    'option': 'value_integer',
    'number': 'value_integer',
    'text': 'value_text',
    'date': 'value_date',
    'model': 'value_reference',
    'selection': 'value_text',
    'document': 'value_reference',
    'hidden': 'value_text',
}


class WebsiteApplicationInformation(models.Model):
    """
    Classe permettant de joindre des informations complémentaire au modèle d'application.

    Le but est de pouvoir rajouter des informations de type basique (nombre, chaîne, ...) au modèle d'application
    pouvant servir à la validation de l'application par l'utilisateur back office.
    Ces informations seront enregistrées dans l'application sous le mode 'result' avec le même nom technique que
    l'information d'origine, permettent ainsi de faire des contrôles de cohérence.
    """

    # region Default methods
    def _default_technical_name(self):
        return self.env['ir.sequence'].sudo().next_by_code('application.information.technical.name')

    # endregion

    # region Private attributes
    _name = 'application.information'
    _order = 'website_application_stage_id, website_application_block_id, sequence, id'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name',
                       required=True,
                       translate=True,
                       help="The text of the information asked to the user on the front interface request")

    technical_name = fields.Char(
        string='Technical name',
        required=True,
        help="The name of the field stored to be able to reference it in other models",
        default=_default_technical_name
    )

    mode = fields.Selection(
        string="Mode",
        selection=INFORMATION_MODES,
        required=True,
        default='query'
    )

    type = fields.Selection(
        string="Type",
        selection=INFORMATION_TYPES,
        required=True,
        help="""'number': number input field\n
            'text': one-line text input field\n
            'option': radio button to get a boolean value\n
            'selection': selection box with custom choice values\n
            'date': date input field\n
            'document': document input field\n
            'explanation': informative html field\n
            'model': selection box with values from corresponding model\n
            'hidden': hidden input field"""
    )

    description = fields.Char(string="Description",
                              help="Description shown to front users",
                              translate=True)

    text_choices = fields.Char(string="Possible choices",
                               translate=True)

    text_explanation = fields.Html(string="Explanation text",
                                   translate=True)

    model_id = fields.Many2one('ir.model', string='Model')

    model = fields.Char(related='model_id.model', readonly=True)

    domain = fields.Char(string="Model domain", default='[]')

    model_relational_field_id = fields.Many2one(
        string="Relational field",
        comodel_name='ir.model.fields',
        domain="[('model', '=', model), "
               "('ttype', 'in', ['many2one', 'many2many', 'one2many']), "
               "'|', ('relation', '=', 'res.users'), ('relation', '=', 'res.partner')]")

    sequence = fields.Integer(string="Sequence")

    website_application_stage_id = fields.Many2one(
        string="Stage",
        comodel_name='website.application.stage',
    )

    website_application_block_id = fields.Many2one(
        string="Block",
        comodel_name='website.application.block',
    )

    document_type_id = fields.Many2one(
        string="Document type",
        comodel_name='ir.attachment.type',
    )

    show_existing_documents = fields.Boolean(
        string="Show existing documents",
        help="Show user's documents of same type already provided by the user",
    )

    allow_multiple_documents_selection = fields.Boolean(
        string="Allow multiple documents selection",
        help="Allow user to select multiple documents in list",
        default=True,
    )

    is_required = fields.Boolean(string="Required", default=True)

    value_integer = fields.Integer()
    value_text = fields.Text()  # will contain (char, text)
    value_reference = fields.Char()
    value_date = fields.Date()
    selection_field_id = fields.Many2one(string="Value",
                                         comodel_name='application.information.choice',
                                         domain="[('technical_name', '=', technical_name)]"
                                         )
    information_choice_id = fields.Many2one(string="Value",
                                            comodel_name='application.information.choice',
                                            domain="["
                                                   "('technical_name', '=', technical_name),"
                                                   "('reference', 'ilike', model),"
                                                   "]",
                                            compute="_compute_information_choice_id",
                                            inverse="_compute_value_reference",
                                            )
    reference_field_id = fields.Reference(string="Value",
                                          selection='_reference_models',
                                          compute="_compute_reference_field_id",
                                          )

    value = fields.Char(string="Value", compute="_compute_value")

    help_image = fields.Binary(string="Help image", help="Image shown on mouse hover to help front user", copy=False)
    # endregion

    # region Fields method
    @api.model
    def _reference_models(self):
        # On liste les modèles demandés dans les informations requises du modèle de téléservice
        template_id = self.env.context.get('website_application_template_id', False)
        template = False
        if template_id:
            template = self.env['website.application.template'].browse(template_id)

        if template and template.application_informations:
            return [(info.model_id.model, info.model_id.name)
                    for info in template.application_informations
                    if info.type in ['model', 'document']]
        else:
            return []

    def _compute_value(self):
        for rec in self:
            if rec.mode == 'result':
                value = rec.get_by_record()
                if value and isinstance(value, models.BaseModel):
                    rec.value = value.name_get()[0][1]
                elif isinstance(value, bool) and rec.type == 'option':
                    rec.value = INFORMATION_OPTION_VALUES[value]
                elif isinstance(value, (int, str)):
                    rec.value = value
                else:
                    rec.value = False

    @api.depends('type', 'mode', 'technical_name', 'value_reference')
    def _compute_information_choice_id(self):
        for rec in self:
            if rec.type in ['model', 'document']:
                if rec.mode == 'result':
                    # On crée les choix s'ils n'existent pas
                    domain = []
                    query = self.env['application.information'].search([
                        ('mode', '=', 'query'),
                        ('technical_name', '=', rec.technical_name)
                    ])

                    if query.model_relational_field_id:
                        if query.model_relational_field_id.relation == 'res.partner':
                            domain.append((
                                query.model_relational_field_id.name, '=', self.env.context.get('applicant_partner_id')
                            ))
                        if query.model_relational_field_id.relation == 'res.users':
                            domain.append(
                                (query.model_relational_field_id.name, '=', self.env.context.get('applicant_id')))

                        if query.domain:
                            domain += safe_eval(query.domain)

                    for choice in self.env[rec.model].search(domain):
                        information_choice = self.env['application.information.choice'].search([
                            ('reference', '=', '%s,%d' % (choice._name, choice.id)),
                            ('technical_name', '=', rec.technical_name),
                            ('information_id', '=', query.id),
                        ])
                        if not information_choice:
                            self.env['application.information.choice'].create({
                                'name': choice.name_get()[0][1],
                                'technical_name': rec.technical_name,
                                'information_id': query.id,
                                'reference': '%s,%d' % (rec.model, choice.id),
                            })

                    if rec.value_reference:
                        rec.information_choice_id = self.env['application.information.choice'].search([
                            ('reference', '=', rec.value_reference)
                        ])
            else:
                rec.information_choice_id = False

    @api.depends('information_choice_id')
    def _compute_reference_field_id(self):
        for rec in self:
            rec.reference_field_id = rec.information_choice_id.reference

    def _compute_value_reference(self):
        for rec in self:
            if rec.mode == 'result' and rec.type in ['model', 'document'] and rec.information_choice_id:
                rec.value_reference = rec.information_choice_id.reference
            else:
                rec.value_reference = ''

    # endregion

    # region Constrains and Onchange
    @api.multi
    @api.constrains('model_id', 'model_relational_field_id')
    def _check_model_field(self):
        """Check if model_id contains relational field.

        :raise: odoo.exceptions.ValidationError if the name is empty
        """
        for rec in self:
            if rec.type == 'model' and rec.model_id and rec.model_relational_field_id:
                if rec.model_relational_field_id not in rec.model_id.field_id:
                    raise ValidationError(_("Relational field must be one of model's fields"))

    @api.multi
    @api.constrains('technical_name')
    def _check_technical_name(self):
        """Check if technical_name is valid.

        :raise: odoo.exceptions.ValidationError if the technical_name contains special characters other than '_' or if
        an information of mode query already exists with that technical name
        """
        for rec in self:
            if not re.match("^[a-z0-9_]*$", rec.technical_name):
                raise ValidationError(_("Technical name must only contain lowercase letters, numbers and underscores"))

            if rec.mode == 'query':
                count = self.search_count([('mode', '=', 'query'),
                                           ('technical_name', '=', rec.technical_name),
                                           ('id', '!=', rec.id)])
                if count:
                    raise ValidationError(_("Technical name must be unique"))

    @api.constrains('value_reference')
    def _check_value_reference(self):
        """Check if value_reference is of type model,id.

        :raise: odoo.exceptions.ValidationError if the value_reference is not in the right format or if the model
        doesn't exist or if the reference doesn't exist
        """
        for rec in self:
            if rec.type in ['model', 'document'] and rec.value_reference:
                if len(rec.value_reference.split(',')) != 2:
                    raise ValidationError(_("Value must be 'model,id'"))

                model, resource_id = self.value_reference.split(',')
                if not self.env['ir.model'].search([('model', '=', model)]):
                    raise ValidationError(_("Model must exist"))
                if not resource_id.isdigit():
                    raise ValidationError(_("Reference must be an integer"))

    @api.onchange('selection_field_id')
    def _on_change_selection_field_id(self):
        if self.type == 'selection':
            self.value_text = self.selection_field_id.name

    @api.onchange('type', 'document_type_id')
    def _on_change_type(self):
        if self.type == 'document':
            self.model_id = self.env['ir.model'].search([('model', '=', 'ir.attachment')])
            self.model_relational_field_id = self.env['ir.model.fields'].search([
                ('model', '=', 'ir.attachment'),
                ('name', '=', 'user_id'),
            ])
            self.domain = "[('status', 'in', ['to_check', 'valid']),('document_type_id', '=', %d)]" \
                          % self.document_type_id.id

        if self.type == 'explanation':
            self.is_required = False

    @api.constrains('type', 'is_required')
    def _check_type_required(self):
        for rec in self:
            if rec.type == 'explanation' and rec.is_required:
                raise ValidationError(_('An explanation information can not be required'))

    # endregion

    # region CRUD (overrides)
    @api.multi
    def write(self, values):
        for rec in self:
            mode = values.get('mode', False) or rec.mode
            if mode == 'query' and values.get('technical_name', False):
                # Change all the informations of mode result with the old technical name
                self.search([
                    ('mode', '=', 'result'),
                    ('technical_name', '=', rec.technical_name)]) \
                    .write({'technical_name': values['technical_name']})

        return super(WebsiteApplicationInformation, self).write(self._update_values(values))

    # endregion

    # region Actions
    # endregion

    # region Model methods
    def get_type_to_field(self, field_type):
        """
        Return the field corresponding to a type.

        :param field_type: the type of field
        :return: the field corresponding to the type
        """
        return TYPE2FIELD.get(field_type)

    @api.multi
    def _update_values(self, values):
        mode = values.get('mode', False)
        if not mode:
            if self:
                info = self[0]
                mode = info.mode
            else:
                mode = self._fields['mode'].default(self)

        if not mode or mode == 'query':
            return values

        value = values.pop('value', None)
        if value is None:
            return values

        type = values.get('type', False)
        if not type:
            if self:
                info = self[0]
                type = info.type
            else:
                type = self._fields['type'].default(self)

        field = self.get_type_to_field(type)
        if not field:
            raise UserError(_('Invalid type'))

        if field == 'value_reference':
            reference = safe_eval(value)
            if isinstance(reference, int):
                value = '%s,%d' % (self.model, reference)

        values[field] = value
        return values

    @api.multi
    def get_by_record(self):
        self.ensure_one()
        if self.type in ('text', 'selection', 'hidden'):
            return self.value_text
        elif self.type == 'option':
            return bool(self.value_integer)
        elif self.type == 'number':
            return self.value_integer
        elif self.type == 'date':
            return self.value_date
        elif self.type in ['model', 'document']:
            if not self.value_reference:
                return False
            if len(self.value_reference.split(',')) != 2:
                return False
            model, resource_id = self.value_reference.split(',')
            return self.env[model].browse(int(resource_id)).exists()
        return False

    def get_model_choices(self, user):
        if self.type not in ['model', 'document'] or not self.model_id:
            return []

        # Ajout de la restriction selon le champ relationnel
        relational_domain = []
        if self.model_relational_field_id:
            if self.model_relational_field_id.relation == 'res.partner':
                value = user.partner_id.id
            if self.model_relational_field_id.relation == 'res.users':
                value = user.id

            if self.model_relational_field_id.ttype in ['one2many', 'many2many']:
                operator = 'ilike'
            else:
                operator = '='

            relational_domain = [(self.model_relational_field_id.name, operator, value)]

        domain = expression.AND([relational_domain, ast.literal_eval(self.domain)])

        return self.env[self.model_id.model].search(domain)

    @api.multi
    def get_information(self, info):
        information_rec = self.filtered(
            lambda a: a.technical_name == info.technical_name and a.type == info.type)
        if information_rec:
            return information_rec

        return None
    # endregion


class WebsiteApplicationInformationChoice(models.Model):
    """Pseudo object, used to create temporary choices for application informations of type 'selection'."""

    # region Private attributes
    _name = 'application.information.choice'
    _order = 'id asc'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Choice')
    technical_name = fields.Char(string='Technical name')
    information_id = fields.Many2one(string='Linked query information', comodel_name='application.information')
    reference = fields.Char()
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
    pass
