# 1 : imports of python lib
import logging
from datetime import datetime

import pytz

# 2 :  imports of openerp
from odoo import models, fields, api, exceptions, _
from odoo.osv import expression

_logger = logging.getLogger(__name__)
APPLICATION_TEMPLATE_STATES = [('active', 'Active'), ('inactive', 'Inactive')]
TERMS_LINK_TARGET_TYPES = [('url', 'Page'), ('document', 'Document')]


class ApplicationTemplate(models.Model):
    """
    Classe permettant de construire des modèles d'applications.

    Le but est de ne pas avoir à redévelopper à chaque demande particulière sur un téléservice.
    On souhaite pouvoir déclarer dans le système un modèle de téléservice en paramétrant pour ce dernier :
    ->Un libellé (texte du lien hyper texte sur le front)
    ->Une description
    ->Une (des) catégorie(s) de partenaire associée(s)
    ->Un (des) document(s) justificatif(s)
    ->Une période de publication sur le front
    ->Un (des) champs de saisie de type texte (libellé/valeur) qui seront renseignés dans la demande
    ->Une fonctionnalité? (ex : Demande de carte)
    ->Métier
    ->Modèles de mails (acceptation, refus, demande etc.)
    ->Commentaire

    Idéalement, on ne peut créer deux téléservices actifs en même temps pour une même fonctionnalité/métier
    et pour des catégories d'usagers identiques.
    """

    # region Private attributes
    _name = 'website.application.template'
    _inherit = ['application.type', 'mail.thread']
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name',
                       required=True,
                       index=True,
                       translate=True,
                       help="The text of the application link on the front interface")
    description = fields.Text(string='Description',
                              translate=True,
                              help="Description of the application")
    is_recipient_to_select = fields.Boolean(string="Selection of a recipient")
    recipient_domain = fields.Char(string="Recipient domain", default='[]')

    attachment_types = fields.Many2many(string="Required documents",
                                        comodel_name='ir.attachment.type',
                                        track_visibility='onchange')
    application_informations = fields.Many2many(string="Other data",
                                                comodel_name='application.information',
                                                domain="[('mode', '=', 'query')]",
                                                track_visibility='onchange')
    beginning_date = fields.Date(string='Beginning date',
                                 default=fields.Date.context_today,
                                 track_visibility='onchange')
    ending_date = fields.Date(string='Ending date',
                              track_visibility='onchange')
    is_active_all_day = fields.Boolean(string="Is active all day long", default=True)
    opening_hour = fields.Float(string="Opening hour")
    closing_hour = fields.Float(string="Closing hour")

    functionality_id = fields.Many2one(string='Functionality', comodel_name='application.functionality', required=True)
    multiple_requests_allowed = fields.Boolean(string="Allow multiple requests")

    ask_partner_informations = fields.Boolean(string="Partner informations")

    subscription_category_partner_ids = fields.Many2many(
        string="Partner categories",
        comodel_name='subscription.category.partner',
        track_visibility='onchange')

    state = fields.Selection(
        string="State",
        selection=APPLICATION_TEMPLATE_STATES,
        compute='_compute_state',
        search='_search_state',
        store=False,
        help="""'active': this application template is available to front users\n
            'inactive': this application template is not available to front users"""
    )
    application_front_image = fields.Binary(
        string="Image used in applications list",
    )
    show_terms_link = fields.Boolean(string="Terms and conditions link")
    terms_checkbox_label = fields.Char(string="Checkbox label",
                                       default=lambda self: _("I have read and accepted the"), translate=True)
    terms_link_label = fields.Char(string="Link label", default=lambda self: _("terms and conditions"), translate=True)
    terms_link_target_type = fields.Selection(selection=TERMS_LINK_TARGET_TYPES)
    terms_link_target_url = fields.Char(track_visibility='onchange')
    terms_link_target_document = fields.Many2one(
        comodel_name="ir.attachment",
        domain="[('document_type_id.technical_name', '=', 'terms_and_conditions'), ('public', '=', True)]",
        track_visibility='onchange'
    )

    auto_validation = fields.Boolean(string="Validate application automatically")

    validation_action_id = fields.Many2one(comodel_name='ir.actions.server',
                                           string="Validation action",
                                           domain="[('model_id.model', '=', 'website.application')]",
                                           help="Function to call on application's validation")

    # endregion

    # region Fields method
    @api.model
    def _search_state(self, operator, value):
        """
        Allow to perform a fast search on state field (used to find rule that can be executed).

        :param operator: opérateur de recherche
        :param value: valeur recherchée ('active' ou 'disabled' ou 'inactive')
        :return: Retourne un domain de recherche correspondant à la recherche sur le champ calculé state
        """
        computed_today = fields.Date.today()
        now = datetime.now(pytz.UTC).astimezone(pytz.timezone('Europe/Paris'))
        computed_hour = now.hour + now.minute / 60. + now.second / 3600.

        # positive search domain
        search_date_valid = ['&',
                             '|', ('beginning_date', '=', False), ('beginning_date', '<=', computed_today),
                             '|', ('ending_date', '=', False), ('ending_date', '>=', computed_today)]
        search_hour_valid = ['|',
                             ('is_active_all_day', '=', True),
                             '&', '&',
                             ('is_active_all_day', '=', False),
                             ('opening_hour', '<=', computed_hour),
                             ('closing_hour', '>=', computed_hour)]
        search_domain = []
        if value == 'active':
            search_domain = expression.AND([search_date_valid, search_hour_valid])
        elif value == 'inactive':
            search_domain = expression.OR(
                [[expression.NOT_OPERATOR] + search_date_valid,
                 [expression.NOT_OPERATOR] + search_hour_valid])

        # en cas de recherche inverse, inverser le domain (exemple '!=' de False)
        if search_domain and operator in expression.NEGATIVE_TERM_OPERATORS:
            search_domain = [expression.NOT_OPERATOR] + search_domain

        return search_domain

    # endregion

    # region Constrains and Onchange
    @api.constrains('functionality_id', 'application_type', 'subscription_category_partner_ids',
                    'beginning_date', 'ending_date')
    def check_unicity(self):
        model = self.env['website.application.template']
        for rec in self:
            if not rec.beginning_date:
                return

            templates = model.search([
                ('functionality_id', '=', rec.functionality_id.id),
                ('application_type', '=', rec.application_type),
                ('id', '!=', rec.id)
            ])

            for template in templates:
                if not len(list(set(rec.subscription_category_partner_ids).symmetric_difference(
                        set(template.subscription_category_partner_ids)))):

                    if rec.beginning_date <= (template.ending_date or rec.beginning_date) \
                            and (rec.ending_date or template.beginning_date) >= template.beginning_date:
                        raise exceptions.ValidationError(
                            _("You cannot have two templates of same functionality/application type/partner "
                              "category on a same period. (see template #{} named '{}')"
                              .format(template.id, template.name)))

    @api.constrains('is_active_all_day', 'opening_hour', 'closing_hour')
    def check_time_values(self):
        """
        Check the consistency of time hours.

        :return: nothing
        :raise: Validation error if hours not set or if opening hour superior to closing hour
        """
        for rec in self:
            if not rec.is_active_all_day:
                # KO si les heures renseignées sont les mêmes
                if rec.closing_hour == rec.opening_hour:
                    raise exceptions.ValidationError(_("Beginning and ending hours must be different"))

                # KO si l'heure de début n'est pas valide
                if rec.opening_hour < 0 or rec.opening_hour > 23.99:
                    raise exceptions.ValidationError(_("Enter a valid beginning hour"))

                # KO s'il y a une heure de début sans heure de fin , ou si l'heure de fin n'est pas valide
                if (rec.opening_hour and not rec.closing_hour) or \
                        (rec.closing_hour and (rec.closing_hour < 0 or rec.closing_hour > 23.99)):
                    raise exceptions.ValidationError(_("Enter a valid closing hour"))

                # KO si l'heure de début est supérieure à l'heure de fin
                if rec.opening_hour > rec.closing_hour:
                    raise exceptions.ValidationError(_("Opening hour must be inferior to closing hour"))

    @api.constrains('beginning_date', 'ending_date')
    def check_date_values(self):
        """
        Check the consistency of date values.

        :return: nothing
        :raise: Validation error if beginning date not set or if beginning date superior to ending date
        """
        for rec in self:
            # KO si la date de fin est renseignée mais inférieure à la date de début
            if rec.ending_date and rec.beginning_date and rec.beginning_date > rec.ending_date:
                raise exceptions.ValidationError(_("Beginning date must be inferior to ending date"))

    @api.depends('beginning_date', 'ending_date', 'is_active_all_day', 'opening_hour', 'closing_hour')
    def _compute_state(self):
        """
        Compute the application template state.

        'active': this application template is visible to front users
        'inactive': this application template is not visible to front users
        :return:
        """
        now = datetime.now(pytz.UTC).astimezone(pytz.timezone('Europe/Paris'))
        computed_hour = now.hour + now.minute / 60. + now.second / 3600.

        for rec in self:
            state = 'active'
            if rec.beginning_date and rec.beginning_date > fields.Date.today():
                state = 'inactive'
            elif rec.ending_date and rec.ending_date < fields.Date.today():
                state = 'inactive'
            elif not rec.is_active_all_day and rec.opening_hour > computed_hour:
                state = 'inactive'
            elif not rec.is_active_all_day and rec.closing_hour < computed_hour:
                state = 'inactive'
            rec.state = state

    # endregion

    # region CRUD (overrides)
    @api.multi
    def copy(self, default=None):
        default = dict(default or {})

        default['beginning_date'] = False
        return super(ApplicationTemplate, self).copy(default)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
