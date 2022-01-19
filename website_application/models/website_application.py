import re

from odoo import models, fields, api, exceptions, _
from odoo.osv import expression
from ..config import config

INFORMATION_SAME_ADDRESS = [('no_same_address', "unique address"),
                            ('same_address_warning', "same address warning"),
                            ('same_address_accepted', "same address accepted")]


class WebsiteApplication(models.Model):
    """Class of the applications. Can be inherited to add more types."""

    # region Private attributes
    _name = 'website.application'
    _inherit = ['mail.thread']
    _order = 'id desc'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Reference', readonly=True)
    website_application_template_id = fields.Many2one(string='Type', comodel_name='website.application.template')
    auto_validation = fields.Boolean(related='website_application_template_id.auto_validation', readonly=True)
    validation_action_id = fields.Many2one(comodel_name='ir.actions.server',
                                           related='website_application_template_id.validation_action_id',
                                           readonly=True)
    functionality_id = fields.Many2one(
        comodel_name='application.functionality',
        related='website_application_template_id.functionality_id',
        readonly=True)
    application_type = fields.Selection(
        related='website_application_template_id.application_type',
        readonly=True)
    state = fields.Selection(string='State', selection=config.STATES, default='new', copy=False)
    applicant_id = fields.Many2one(string='Applicant', comodel_name='res.users')
    applicant_partner_id = fields.Many2one(
        string="Applicant partner",
        comodel_name='res.partner',
        compute='_compute_applicant_partner_id',
        store=True)
    recipient_id = fields.Many2one(string='Recipient', comodel_name='res.partner', required=True)

    applicant_address = fields.Char(string="Address", related='recipient_id.better_contact_address', store=True)

    same_address = fields.Selection(string="same address", selection=INFORMATION_SAME_ADDRESS,
                                    compute='_compute_same_address',
                                    search='_search_same_address')

    address_duplication = fields.Many2many(string="Address duplication",
                                           comodel_name='website.application',
                                           compute='_compute_address_duplication',
                                           store=False)

    date = fields.Datetime(string='Submit date', default=fields.Datetime.now, required=True)
    messages_ids = fields.One2many(string='Messages', comodel_name='website.application.message',
                                   inverse_name='application_id',
                                   track_visibility='onchange')
    new_messages = fields.Boolean(string='New message', compute='get_if_new_message', store=True)

    attachment_ids = fields.Many2many(string="Documents",
                                      comodel_name='ir.attachment',
                                      track_visibility='onchange')

    application_information_ids = fields.Many2many(string="Required informations",
                                                   track_visibility='onchange',
                                                   comodel_name='application.information',
                                                   domain="[('id', 'in', [])]")

    value_removal_reason = fields.Char(string="Reason",
                                       compute="_compute_value_required_informations",
                                       store=True)

    value_date = fields.Char(string="Date of the request", compute="_compute_value_required_informations", store=True)
    value_refund_type = fields.Char(string="Refund type", compute="_compute_value_required_informations", store=True)
    value_date_changing_establishment = fields.Char(string="Date of changing establishment",
                                                    compute="_compute_value_required_informations",
                                                    store=True)

    value_date_changing_residence = fields.Char(string="Date of changing residence",
                                                compute="_compute_value_required_informations",
                                                store=True)

    # endregion

    # region Fields method
    @api.depends('messages_ids')
    def get_if_new_message(self):
        for rec in self:
            new_messages = rec.messages_ids.filtered(lambda r: not r.is_read)
            if len(new_messages) >= 1:
                rec.new_messages = True
            else:
                rec.new_messages = False

    @api.depends('applicant_id')
    def _compute_applicant_partner_id(self):
        """Retrouve le partner du user."""
        for rec in self:
            if rec.applicant_id:
                user = self.env['res.users'].browse(rec.applicant_id.id)
                rec.applicant_partner_id = user.partner_id.id
            else:
                rec.applicant_partner_id = rec.recipient_id.id

    @api.constrains('application_information_ids')
    @api.depends('application_information_ids')
    def _compute_value_required_informations(self):
        """Get value of the required informations field for pivot and graph views."""
        for record in self:
            for rec in record.application_information_ids:
                if rec.technical_name == 'removal_reason':
                    record.value_removal_reason = rec.value

                if rec.technical_name == 'on_date':
                    record.value_date = rec.value

                if rec.technical_name == 'refund_type':
                    record.value_refund_type = rec.value

                if rec.technical_name == 'date_changing_establishment':
                    record.value_date_changing_establishment = rec.value

                if rec.technical_name == 'date_changing_residence':
                    record.value_date_changing_residence = rec.value

    @api.depends('applicant_address', 'website_application_template_id', 'state')
    def _compute_address_duplication(self):
        """
        Compute the field address_duplication.

        Search applications who not allow multi requests and have the same address,
        the same type(website_application_template_id) that the current application.
        """
        all_application = self.env['website.application']
        for application in self.filtered('applicant_address'):
            application.address_duplication = all_application.search([
                ('name', '!=', application.name),
                ('state', 'in', ['new', 'pending', 'accepted']),
                ('applicant_address', '=', application.applicant_address),
                ('website_application_template_id', '=', application.website_application_template_id.id),
                ('website_application_template_id.multiple_requests_allowed', '=', False)])

    @api.depends('address_duplication', 'state')
    def _compute_same_address(self):
        """Define the selection of same_address."""
        for application in self:
            same_address = 'no_same_address'
            if bool(application.address_duplication):
                if application.state in ['new', 'pending']:
                    same_address = 'same_address_warning'
                elif application.state == 'accepted':
                    same_address = 'same_address_accepted'
            application.same_address = same_address

    def _search_same_address(self, operator, value):
        search_domain = []
        all_application = self.search([]).filtered('applicant_address').filtered(lambda r: r.state != 'rejected')
        ids = []
        for application in all_application:
            application_temp = all_application.search([
                ('name', '!=', application.name),
                ('state', 'in', ['new', 'pending', 'accepted']),
                ('applicant_address', '=', application.applicant_address),
                ('website_application_template_id', '=', application.website_application_template_id.id),
                ('website_application_template_id.multiple_requests_allowed', '=', False)])

            if application_temp:
                for k in range(0, len(application_temp)):
                    ids.append(application_temp[k].id)

        if value == 'no_same_address':
            search_domain = ['&', ('state', 'in', ['new', 'pending', 'accepted']), ('id', 'not in', ids)]
        if value == 'same_address_warning':
            search_domain = ['&', ('state', 'in', ['new', 'pending']), ('id', 'in', ids)]
        if value == 'same_address_accepted':
            search_domain = ['&', ('state', '=', 'accepted'), ('id', 'in', ids)]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            search_domain = [expression.NOT_OPERATOR] + search_domain

        return search_domain

    @api.onchange('website_application_template_id')
    def _onchange_website_application_template(self):
        """Add default required informations with default values."""
        if not self.website_application_template_id:
            return

        self.application_information_ids = False

        query_informations = self.website_application_template_id.application_informations
        informations_ids = []

        for query_information in query_informations:
            if query_information.type == 'explanation':
                continue

            new_information = query_information.copy({
                'mode': 'result',
                'value': ''
            })

            if query_information.type == 'selection':
                for choice in query_information.text_choices.split(','):
                    information_choice = self.env['application.information.choice'].search([
                        ('name', '=', choice),
                        ('technical_name', '=', query_information.technical_name),
                        ('information_id', '=', query_information.id),
                    ])
                    if not information_choice:
                        self.env['application.information.choice'].create({
                            'name': choice,
                            'technical_name': query_information.technical_name,
                            'information_id': query_information.id,
                        })

            informations_ids.append(new_information.id)

        return {
            'domain': {'application_information_ids': [
                ('id', 'in', informations_ids),
            ]},
        }

    # endregion

    # region Constrains and Onchange
    @api.onchange('applicant_id')
    def _onchange_applicant_id(self):
        """Domain of the field recipient_id."""
        res = {}
        if self.applicant_id and self.applicant_partner_id:
            partners = self.applicant_partner_id + \
                       self.applicant_id.child_ids.filtered(lambda r: r.type == 'contact') + \
                       self.applicant_partner_id.search(
                           [('search_field_all_foyers_members', 'in', self.applicant_partner_id.id)])
            res['domain'] = {'recipient_id': [('id', 'in', partners.ids)]}
        return res

    @api.constrains('state')
    def _check_required_data(self):
        """Vérifie les champs nécessaire en fonction du modèle.

        :return: None or raise an exception
        """
        for rec in self:
            list_error_message = []

            if rec.state == "accepted":
                rec.check_documents(list_error_message)
                rec.check_informations(list_error_message)

            if list_error_message:
                raise exceptions.ValidationError('\n'.join(list_error_message) + '\n')

    @api.model
    def check_documents(self, list_error_message):
        template = self.env['website.application.template'].browse(self.website_application_template_id.id)
        attachment_types_given = self.attachment_ids.mapped('document_type_id.id')

        for attachment_type_required in template.attachment_types:
            if attachment_type_required.id not in attachment_types_given:
                list_error_message.append(
                    _("You must provide a document of type " + attachment_type_required.name))

        # All submitted documents must have been validated before acceptation
        if self.attachment_ids:
            for status in self.attachment_ids.mapped('status'):
                if status != 'valid':
                    list_error_message.append(
                        _("Attachments must be validated before accepting the request"))
                    break

    @api.multi
    def check_informations(self, list_error_message):
        self.ensure_one()
        template = self.env['website.application.template'].browse(self.website_application_template_id.id)
        informations_required = template.application_informations.filtered(
            lambda i: i.is_required and i.type != 'document')

        for information_required in informations_required:
            info = self.application_information_ids.get_information(information_required)
            if info is None or not info.value:
                list_error_message.append(_("The information '{}' is missing").format(information_required.name))

    @api.constrains('recipient_id', 'website_application_template_id', 'state')
    def check_application_unicity(self):
        """Vérifie l'unicité des demandes.

        :param vals: les données à enregistrer
        :return: Validationerror ou rien
        """
        # On regarde le paramètre correspondant sur le modèle
        template = self.env['website.application.template'].browse(self.website_application_template_id.id)

        if template and not template.multiple_requests_allowed:
            nb_requests = self.search_count([
                ('recipient_id', '=', self.recipient_id.id),
                ('state', '!=', 'rejected'),
                ('website_application_template_id', '=', self.website_application_template_id.id),
                ('id', '!=', self.id),
            ])

            if nb_requests:
                raise exceptions.ValidationError(
                    _("You have already submitted this kind of request."))

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """Override create to create the reference."""
        sequence = self.env.ref('website_application.seq_website_application')
        vals['name'] = sequence.sudo().next_by_id()

        result = super(WebsiteApplication, self).create(vals)

        # On regarde s'il y a une action à effectuer sur le modèle
        if result.auto_validation:
            try:
                # On valide le téléservice (envoi de mail)
                result.action_accept()
            except Exception:
                # En cas d'erreur, on repasse le téléservice à 'nouveau'
                # pour une validation en back office
                result.state = 'new'

        return result

    # endregion

    # region Actions
    @api.multi
    def action_pending(self):
        """Set the application to pending and send a mail."""
        self.ensure_one()
        self.state = 'pending'
        template_id = self.env.ref('website_application.email_application_pending')
        template_id.send_mail(self.id, force_send=True)

    @api.multi
    def action_accept(self):
        """Set the application to accepted and send a mail."""
        self.ensure_one()
        self.state = 'accepted'
        # On déclenche l'action de validation s'il y en a une
        self.action_template_validation_action()
        # Si la demande est acceptée, on force les messages en lus pour ne pas bloquer l'envoi du mail
        self.action_messages_read()
        template_id = self.env.ref('website_application.email_application_accepted')
        template_id.sudo().send_mail(self.id, force_send=True)

    @api.multi
    def action_reject(self):
        """Set the application to rejected and send a mail."""
        self.ensure_one()
        self.state = 'rejected'
        template_id = self.env.ref('website_application.email_application_rejected')
        template_id.send_mail(self.id, force_send=True)

    @api.multi
    def action_messages_read(self):
        """Make all messages read."""
        self.ensure_one()
        for message in self.messages_ids:
            message.is_read = True
            self.get_if_new_message()

    @api.multi
    def action_template_validation_action(self):
        """Trigger the action set on template."""
        self.ensure_one()
        if self.validation_action_id:
            context = {
                'active_model': 'website.application',
                'active_id': self.id,
                're': re,
            }
            self.validation_action_id.with_context(context).run()

    # endregion

    # region Model methods
    # endregion

    pass
