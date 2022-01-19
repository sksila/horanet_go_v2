# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api, exceptions, _
from ..config import config

_logger = logging.getLogger(__name__)


class TCOInscription(models.Model):
    """Class of TCO inscriptions school transports."""

    # region Private attributes
    _name = 'tco.inscription.transport.scolaire'
    _inherit = ['ir.needaction_mixin', 'mail.thread']
    _sql_constraints = [('unity', 'CHECK(1=1)',
                         _('An inscription already exist for the same period, recipient, responsable'))]

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Inscription reference", readonly=True, copy=False)
    period_id = fields.Many2one(string="Period", comodel_name='tco.inscription.period', required=True)
    date_start = fields.Date(related='period_id.date_start', readonly=True)
    date_end = fields.Date(related='period_id.date_end', readonly=True)

    responsible_id = fields.Many2one(string="Responsible", comodel_name='res.partner', required=True)
    responsible_user_id = fields.Many2one(string='Responsible user', comodel_name='res.users', store=False,
                                          compute='compute_responsible_user_id', search='_search_responsible_user_id')
    responsable_address = fields.Char(string="Address", related='responsible_id.better_contact_address',
                                      readonly=True)
    responsible_city = fields.Many2one(string="City", related='responsible_id.city_id', store=True)

    assist = fields.Char(string='Assist')
    assist_phone = fields.Char(string='Assist phone number')
    assist2 = fields.Char(string='Second assist')
    assist_phone2 = fields.Char(string='Second assist phone number')

    recipient_id = fields.Many2one(string="Recipient", comodel_name='res.partner', required=False, readonly=False,
                                   domain="[('search_field_all_foyers_members', 'in', responsible_id)]")
    recipient_address = fields.Char(string="Address", related='recipient_id.better_contact_address', readonly=True)
    recipient_birthdate = fields.Date(string="Birthdate", related='recipient_id.birthdate_date')
    recipient_age = fields.Float(compute='_compute_recipient_age')
    display_recipient_age = fields.Char(string='Age', compute='_compute_display_recipient_age', store=False)

    status = fields.Selection(string="Status", selection=config.INSCRIPTION_STATUS, default='draft', copy=False)

    regime = fields.Selection(string="Regime", selection=config.INSCRIPTION_REGIME)
    school_establishment_id = fields.Many2one(string="Establishment", comodel_name='horanet.school.establishment')
    school_cycle = fields.Many2one(string="School cycle", comodel_name='horanet.school.cycle',
                                   domain="[('computed_establishment_ids', 'in', [school_establishment_id])]")
    school_grade_id = fields.Many2one(string='School grade', comodel_name='horanet.school.grade')
    establishment_city_id = fields.Many2one(string="School city", related='school_establishment_id.city_id', store=True)

    is_student = fields.Boolean(string="Is student")
    is_automatic_payment = fields.Boolean(string="Automatic payment", default=False)
    transport_titre = fields.Selection(string="Transport title", selection=config.INSCRIPTION_TRANSPORT_TITRE)
    invoice_period = fields.Selection(string="Invoice period", selection=config.INSCRIPTION_INVOICE_PERIOD)
    compte_id = fields.Many2one(string="Bank account", comodel_name='res.partner.bank',
                                domain="[('partner_id', '=', responsible_id)]")
    has_badge = fields.Boolean(string="Has badge", default=False)
    badge_id = fields.Many2one(string="Badge", comodel_name='partner.contact.identification.medium',
                               domain="[('partner_id','=',recipient_id)]")

    family_quotient = fields.Integer(string="Family quotient")
    is_allowing_picture = fields.Boolean(string="Is allowing pictures", default=False)
    is_allowing_hospitalization = fields.Boolean(string='Is allowing hospitalization', default=False)

    line_forward_id = fields.Many2one(string="Forward line", comodel_name='tco.transport.line',
                                      domain="[('line_type', '=', 'outward'),"
                                             "('line_stop_ids', 'in', transport_stop_aller_id)]")
    line_backward_id = fields.Many2one(string="Backward line", comodel_name='tco.transport.line',
                                       domain="[('line_type', '=', 'return'),"
                                              "('line_stop_ids', 'in', transport_stop_retour_id)]")
    transport_stop_aller_id = fields.Many2one(string="Inward stop", comodel_name='tco.transport.stop',
                                              domain="[('station_id','=',station_aller_id)]")
    transport_stop_retour_id = fields.Many2one(string="Outward stop", comodel_name='tco.transport.stop',
                                               domain="[('station_id','=',station_retour_id)]")
    station_aller_id = fields.Many2one(string='Forward station', comodel_name='tco.transport.station')
    station_retour_id = fields.Many2one(string='Backward station', comodel_name='tco.transport.station')
    radier_aller_id = fields.Many2one(string="Inward radier", comodel_name='tco.transport.radier')
    radier_retour_id = fields.Many2one(string="Outward radier", comodel_name='tco.transport.radier')

    is_derogation = fields.Boolean(string="Exemption", compute='_compute_derogation', store=True)
    derogation_type = fields.Selection(string="Exemption type", selection=config.INSCRIPTION_DEROGATION, default=None)
    ignore_derogation = fields.Boolean(string="Ignore derogation")
    is_als = fields.Boolean(related='recipient_id.is_als')
    als_responsible_id = fields.Many2one(string="Responsible", comodel_name='res.partner')
    sale_order_ref = fields.Many2one(string="Sale order", comodel_name='sale.order', readonly=True, copy=False)
    invoice_validated = fields.Boolean(string="Invoice validated", compute='_get_invoice_status', store=True)
    refuse_reason = fields.Text(string='Refuse reason', copy=False)

    currency_id = fields.Many2many('res.currency')
    sale_order_total_price = fields.Monetary(string="Amount",
                                             currency_field='currency_id',
                                             compute='_compute_sale_order_total_price',
                                             readonly=True,
                                             store=True)

    school_enrollment_certificate = fields.Many2one(
        string="School enrollment certificate", comodel_name='ir.attachment',
        domain="[('partner_id', '=', recipient_id), \
                 ('document_type_id.technical_name', '=', 'school_enrollment_certificate'), \
                 ('status', 'in', ['to_check', 'valid']), \
                 ('is_expired', '=', False)]",
    )
    school_enrollment_certificate_status = fields.Selection(
        string="Certificate status", related='school_enrollment_certificate.status', readonly=True
    )
    qf_certificate = fields.Many2one(
        string="QF certificate", comodel_name='ir.attachment',
        domain="[('partner_id', '=', responsible_id), \
                 ('document_type_id.technical_name', 'in', ['caf_certificate', 'tax_notice', 'pay_slip']), \
                 ('status', 'in', ['to_check', 'valid']), \
                 ('is_expired', '=', False)]",
    )
    qf_certificate_status = fields.Selection(
        string="Certificate status", related='qf_certificate.status', readonly=True
    )
    address_certificate = fields.Many2one(
        string="Address certificate", comodel_name='ir.attachment',
        domain="[('partner_id', '=', responsible_id), \
                 ('document_type_id.technical_name', 'in', ['proof_of_address', 'tax_notice', 'pay_slip']), \
                 ('status', 'in', ['to_check', 'valid']), \
                 ('is_expired', '=', False)]",
    )
    address_certificate_status = fields.Selection(
        string="Certificate status", related='address_certificate.status', readonly=True
    )
    bank_details = fields.Many2one(
        sting="Bank details", comodel_name='ir.attachment',
        domain="[('partner_id', '=', responsible_id), \
                 ('document_type_id.technical_name', '=', 'bank_details'), \
                 ('is_expired', '=', False)]",
    )
    bank_details_status = fields.Selection(
        string='Bank details status', related='bank_details.status', readonly=True
    )

    # endregion

    # region Fields method
    @api.depends('responsible_id')
    def compute_responsible_user_id(self):
        """Get the responsible user according to the partner."""
        for rec in self:
            rec.responsible_user_id = rec.responsible_id and rec.responsible_id.user_ids and \
                                      rec.responsible_id.user_ids[0] or False

    @api.multi
    @api.depends('recipient_birthdate')
    @api.onchange('recipient_birthdate')
    def _compute_recipient_age(self):
        today = fields.Date.from_string(fields.Date.context_today(self))
        for rec in self:
            if rec.recipient_birthdate:
                birth = fields.Date.from_string(rec.recipient_birthdate)
                nb_years = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                nb_months = 0
                if today.day >= birth.day:
                    if today.month >= birth.month:
                        nb_months = today.month - birth.month
                    else:
                        nb_months = 12 - (birth.month - today.month)
                else:
                    if today.month > birth.month:
                        nb_months = (today.month - birth.month) - 1
                    else:
                        nb_months = 11 - (birth.month - today.month)

                rec.recipient_age = nb_years + (nb_months / 100.)

    @api.multi
    @api.depends('recipient_age')
    def _compute_display_recipient_age(self):
        """Compute the age displayed of the partner."""
        for rec in self:
            if rec.recipient_age:
                nb_year = int(rec.recipient_age)
                nb_month = int((rec.recipient_age % 1) * 100)
                tmp = _("{nb_year} {year_txt}").format(
                    nb_year=nb_year,
                    year_txt=_("Years") if nb_year > 1 else _("Year"))
                if nb_month > 0:
                    tmp += _(" and {nb_month} {month_txt}").format(
                        nb_month=nb_month,
                        month_txt=_("months") if nb_month > 1 else _("month"))

                rec.display_recipient_age = tmp

    @api.model
    def _search_responsible_user_id(self, operator, value):
        """
        Search the responsible user.

        :param operator: operator
        :param value: id of the user
        :return: domain
        """
        value = int(value)
        search_domain = [('responsible_id.user_ids', operator, value)]
        return search_domain

    @api.depends('school_establishment_id', 'recipient_id', 'ignore_derogation')
    def _compute_derogation(self):
        """
        Compute if the request is on derogation.

        :return: boolean
        """
        for rec in self:
            if rec.school_establishment_id and rec.recipient_id and not rec.is_student and not rec.ignore_derogation:
                rec.is_derogation = self.get_is_derogation(rec.school_establishment_id, rec.recipient_id)
            else:
                rec.is_derogation = False

    # Sert à mettre en validé lorsque la facture est validée
    @api.depends('sale_order_ref.invoice_ids', 'sale_order_ref.state', 'sale_order_ref.order_line.invoice_status')
    def _get_invoice_status(self):
        """
        Get the status of the associated invoice.

        We use same fields for the depends as the method
        :meth:`odoo.addons.sale.models.sale._get_invoiced`

        And we use the field computed by the previous method in order to simulate
        an ORM override of the method from another model...
        """
        for rec in self:
            invoice_validated = False
            if rec.sale_order_ref:
                if rec.sale_order_ref.state == 'cancel':
                    rec.write({'status': 'cancelled'})
                elif rec.sale_order_ref.invoice_ids and rec.sale_order_ref.invoice_ids.filtered(
                        lambda r: r.state in ['open', 'paid']):
                    rec.write({'status': 'validated'})
                    invoice_validated = True
            rec.invoice_validated = invoice_validated

    @api.constrains('status')
    @api.depends('status')
    def _compute_sale_order_total_price(self):
        """Get the amount total of the sale order for pivot and graph views."""
        for rec in self:
            if rec.status == 'validated':
                if rec.sale_order_ref:
                    rec.sale_order_total_price = rec.sale_order_ref.amount_total

    # endregion

    # region Constrains and Onchange
    @api.constrains('status')
    def _check_status_constrains(self):
        u"""
        Vérifie si l'inscription peux être modifié en fonction du workflow (status).

        Vérifie la présence des champs

        :return: None or raise an exception
        """
        for rec in self:
            list_error_message = []
            if rec.is_student:
                if rec.invoice_period == 'monthly':
                    list_error_message.append(
                        _("When recipient is a student, you can't select a monthly invoice period"))
                if rec.is_derogation:
                    list_error_message.append(_("When recipient is a student, you can't set derogation"))
                if rec.transport_titre == 'cool':
                    list_error_message.append(_("When recipient is a student, you can't select a COOL transport title"))

            # On ne teste ici que pour le cas ou on passe en "à valider" pour les inscriptions créées en front
            # Car en back on passe automatiquement en "bon de commande"
            if rec.status == 'to_validate' or (rec.status == 'progress' and not self.env.context.get('force_creation')):
                list_error_message = rec.check_status_to_validate_constrains(list_error_message)

            # Ici on ne vérifie que les champs nécessaires à la facturation
            # On passe directement à cette étape en back
            if rec.status == 'progress':
                # Pour la derogation, cela se vérifie seulement en back
                if not self.env.context.get('force_creation') and self.is_derogation and not self.derogation_type:
                    list_error_message.append(_("derogation type missing"))
                list_error_message = rec.check_required_fields_sale_order(list_error_message)

            if list_error_message:
                list_error_message.append(
                    _("Please proceed to make all the requirements before accepting the inscription"))
                raise exceptions.ValidationError('\n'.join(list_error_message) + '\n')

    @api.multi
    def check_status_to_validate_constrains(self, list_error_message):
        """
        Check the fields required to be in status "to validate".

        :param list_error_message: list of error message
        :return: list of error message
        """
        self.ensure_one()
        # On vérifie aussi les champs nécessaires à la facturation, les agents ne peuvent pas les deviner
        # On oublie la vérification des documents, impossible en front
        list_error_message = self.with_context({'force_creation': True}) \
            .check_required_fields_sale_order(list_error_message)
        if not self.school_grade_id:
            list_error_message.append(
                _("You must select a school grade"))
        if not self.regime:
            list_error_message.append(_("regime missing"))
        if not self.school_establishment_id:
            list_error_message.append(_("establishment missing"))
        if not self.school_cycle:
            list_error_message.append(_("school cycle missing"))

        return list_error_message

    def check_required_fields_sale_order(self, list_error_message):
        """
        Check the fields required to create the sale order.

        :param list_error_message: list of error message
        :return: list of error message
        """
        if not self.transport_titre:
            list_error_message.append(_("transport titre missing"))
        if not self.invoice_period:
            list_error_message.append(_("invoice period missing"))
        if not self.responsible_user_id:
            list_error_message.append(
                _("You must choose a partner with portal access for an inscription"))
        if not self.recipient_id:
            list_error_message.append(_("recipient missing"))

        # Si on veut créer le SO depuis le wizard, on ignore les documents
        if not self.env.context.get('force_creation'):
            if self.responsible_id.quotient_fam < 1000 and not self.qf_certificate_status == 'valid':
                list_error_message.append(_("A document that validates the QF is required."))
            if not self.school_enrollment_certificate_status == 'valid':
                list_error_message.append(_("A document that validates the school inscription is required."))
            if not self.address_certificate_status == 'valid':
                list_error_message.append(_("A document that validates the address is required."))

        return list_error_message

    @api.constrains('school_cycle', 'school_establishment_id')
    def _check_establishment_cycle_constrains(self):
        u"""
        Vérifie que le cycle de l'école correspond au cycle de l'inscription.

        :return: exception ou kedale
        """
        for rec in self:
            if rec.school_cycle and rec.school_establishment_id:
                establishment_ids = rec.school_cycle.computed_establishment_ids
                if rec.school_establishment_id.id not in establishment_ids.ids:
                    raise exceptions.ValidationError(_("the establishment is not in the selected school cycle"))

    @api.multi
    def _check_unicity(self, vals):
        u"""
        Vérifie l'unicité du model, pour renvoyer un message en cas de doublon.

        :param vals: liste des champs modifiés (en cas de create)
        :return: none or raise an exception
        """
        for rec in self:
            duplicates = self.search([('period_id', '=', vals.get('period_id') or rec.period_id.id),
                                      ('status', 'not in', ['cancelled', 'refused']),
                                      ('responsible_id', '=', vals.get('responsible_id') or rec.responsible_id.id),
                                      ('recipient_id', '=', vals.get('recipient_id') or rec.recipient_id.id),
                                      ('id', '!=', rec.id)], limit=1)
            if duplicates:
                raise exceptions.ValidationError(_("This inscription is a duplicate of '{0}'").format(duplicates[0].id))

    @api.onchange('station_aller_id')
    def _onchange_stop_and_line_forward_id(self):
        """Empty forward stop and line if station is changed."""
        self.transport_stop_aller_id = False
        self.line_forward_id = False

    @api.onchange('station_retour_id')
    def _onchange_stop_and_line_backward_id(self):
        """Empty backward stop and line if station is changed."""
        self.transport_stop_retour_id = False
        self.line_backward_id = False

    @api.onchange('transport_stop_aller_id')
    def _onchange_line_forward_id(self):
        """Select the forward line according to the stop."""
        if self.transport_stop_aller_id:
            self.line_forward_id = self.transport_stop_aller_id and self.transport_stop_aller_id.line_id or False
        else:
            self.line_forward_id = False

    @api.onchange('transport_stop_retour_id')
    def _onchange_line_backward_id(self):
        """Select the backward line according to the stop."""
        if self.transport_stop_retour_id:
            self.line_backward_id = self.transport_stop_retour_id and self.transport_stop_retour_id.line_id or False
        else:
            self.line_backward_id = False

    # Un onchange de plus pour le cycle scolaire
    @api.onchange('school_establishment_id')
    def _onchange_school_establishment_id(self):
        """
        Empty school_cycle when school_establishment_id is changed and set the default cycle if there is only 1.

        Empty all transport related fields.
        Set the domain on school_grade_id
        """
        self.school_cycle = False
        self.station_aller_id = False
        self.station_retour_id = False
        self.transport_stop_aller_id = False
        self.transport_stop_retour_id = False
        self.line_forward_id = False
        self.line_backward_id = False
        if self.school_establishment_id:
            res = {}
            if len(self.school_establishment_id.computed_school_cycle) == 1:
                self.school_cycle = self.school_establishment_id.computed_school_cycle[0]
            if self.school_establishment_id.school_grade_ids:
                ids = self.school_establishment_id.school_grade_ids.ids
                res['domain'] = {'school_grade_id': [('id', 'in', ids)]}
                return res

    # Pour mettre le quotient familial
    @api.onchange('responsible_id')
    def _set_family_quotient(self):
        """To set the default family_quotient for a partner."""
        if self.responsible_id:
            self.family_quotient = self.responsible_id.quotient_fam

    # Les 2 onchanges suivants sont lorsque l'on coche la case "est étudiant"
    @api.onchange('is_student')
    def _is_student_checked(self):
        """When recipient is student, disable derogation and transport title set to cool+ only."""
        if self.is_student:
            self.is_derogation = False
            self.transport_titre = 'cool_plus'
        else:
            # On rappel le compute du dérogation
            self._compute_derogation()

    @api.onchange('invoice_period')
    def _invoice_period_is_student(self):
        """Can't select a monthly invoice period if the recipient is a student."""
        if self.is_student and self.invoice_period == 'monthly':
            self.invoice_period = 'annually'
            return {
                "warning": {"title": _("Warning"),
                            "message": _("If the recipient is a student, you can't select a monthly invoice period")},
            }

    # endregion

    # region CRUD (overrides)
    @api.multi
    def write(self, vals):
        """Override write to check values, before being stored."""
        retour = False
        # On ne vérifie la duplicité que si certains champs sont modifiés
        duplicity_fields = ['period_id', 'status', 'responsible_id', 'recipient_id']
        if set(duplicity_fields).intersection(vals.keys()) and vals.get('status', False) \
                not in ['validated', 'cancelled', 'refused']:
            self._check_unicity(vals)

        updatable_fields = [
            'school_establishment_id', 'school_cycle', 'school_grade_id',
            'is_derogation', 'derogation_type',
            'station_aller_id', 'station_retour_id',
            'transport_stop_aller_id', 'transport_stop_retour_id',
            'line_forward_id', 'line_backward_id', 'radier_aller_id', 'radier_retour_id',
            'has_badge', 'badge_id',
            'regime', 'is_als', 'is_allowing_picture', 'is_allowing_hospitalization'
        ]

        for rec in self:
            # On empêche la modification en état validé et annulé
            # TODO Voir si on peut trouver mieux avec des records rules (déjà essayé -> echec)
            if rec.status in ['draft', 'to_validate'] or vals.get('status', False) in ['cancelled', 'validated'] \
                    or vals.get('sale_order_ref', False) or vals.get('badge_id', False) \
                    or (rec.status == 'validated' and set(vals.keys()) <= set(updatable_fields)):
                # Si étudiant, on n'enregistre que le cool+
                # Obligatoire sinon étant donné que le champ est readonly, odoo ne prend pas la valeur.
                if vals.get('is_student', False):
                    vals['transport_titre'] = 'cool_plus'
                retour = super(TCOInscription, self).write(vals)
            else:
                raise exceptions.ValidationError(_("You cannot modify a validated or a cancelled inscription"))
            # On envoi un mail au changement de statut
            if vals.get('status', False) and not self.env.context.get('ignore_emails', False):
                status = vals.get('status', False)
                if status == 'to_validate':
                    template_id = self.env.ref('tco_inscription_transport_scolaire.email_template_inscription_draft')
                    template_id.sudo().send_mail(rec.id, force_send=True)
                elif status == 'validated':
                    template_id = self.env.ref(
                        'tco_inscription_transport_scolaire.email_template_inscription_validated')
                    template_id.sudo().send_mail(rec.id, force_send=True)
                elif status == 'cancelled':
                    template_id = self.env.ref(
                        'tco_inscription_transport_scolaire.email_template_inscription_cancelled')
                    template_id.sudo().send_mail(rec.id, force_send=True)

        return retour

    @api.model
    def create(self, vals):
        """Override write to check values, before being stored."""
        self._check_unicity(vals)
        # Le nom de l'inscription est une séquence
        sequence = self.env.ref('tco_inscription_transport_scolaire.seq_tco_inscription_transport_scolaire')
        vals['name'] = sequence.sudo().next_by_id()
        # Si étudiant, on n'enregistre que le cool+
        # Obligatoire sinon étant donné que le champ est readonly, odoo ne prend pas la valeur.
        if vals.get('is_student', False):
            vals['transport_titre'] = 'cool_plus'
        return super(TCOInscription, self).create(vals)

    # On met des conditions pour empêcher de suprimer n'importe quoi
    @api.multi
    def unlink(self):
        """
        Override unlink to check values.

        Raise ValidationError if we try to delete a draft or a 'to_validate' inscription.

        :raise ValidationError: if the inscription is not in 'draft' or 'to_validate' status
        """
        for rec in self:
            if rec.status not in ['draft', 'to_validate']:
                raise exceptions.ValidationError(_("You can remove a draft inscription only"))
        return super(TCOInscription, self).unlink()

    # Pour le needaction
    @api.model
    def _needaction_domain_get(self):
        """To have a needaction on the menu. We show to_validate inscriptions."""
        return [('status', '=', 'to_validate')]

    # endregion

    # Region actions
    @api.multi
    def action_see_user(self):
        """Retourne une action qui affiche le partner du responsable."""
        self.ensure_one()
        view = self.env.ref('base.view_users_simple_form')
        return {
            'name': 'User',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.users',
            'type': 'ir.actions.act_window',
            'view_id': view.id,
            'res_id': self.responsible_user_id.id,
            'target': 'current',
        }

    def action_create_user(self):
        u"""Créer le user en se basant sur le template user et sur le partner."""
        self.ensure_one()
        template_citoyen = self.env.ref('horanet_auth_signup.horanet_template_customer').sudo()
        if template_citoyen:
            new_user = template_citoyen.copy({'login': self.responsible_id.email,
                                              'partner_id': self.responsible_id.id,
                                              'firstname': self.responsible_id.firstname,
                                              'lastname': self.responsible_id.lastname,
                                              'lang': self.responsible_id.lang,
                                              'active': True})
            self.responsible_user_id = new_user.id
        else:
            raise exceptions.ValidationError('Template citizen not found')

    @api.multi
    def action_create_saleorder(self):
        """
        Create the sale order.

         by calling the function :meth:`~_create_saleorder` and put the inscription status on 'progress'.
        """
        self.ensure_one()
        if self.status == 'to_validate' or self.status == 'draft':
            self._create_saleorder()
            self.status = 'progress'
            return self.action_show_sale_order()

    @api.multi
    def action_cancel(self):
        """Set the inscription cancelled."""
        self.ensure_one()
        self.status = 'cancelled'

    @api.multi
    def action_show_sale_order(self):
        """Retourne une action qui affiche un sale order."""
        self.ensure_one()
        return {
            'name': 'Sale order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'res_id': self.sale_order_ref.id,
            'target': 'current',
        }

    @api.multi
    def _create_saleorder(self):
        """
        Create the sale order.

        :param family_quotient: family quotient of partner
        :param pricelist_rec: pricelist TCO
        :param product_template_rec: product template TCO
        :param payment_term_rec: payment term TCO
        """
        self.ensure_one()

        so_model = self.env['sale.order']

        # get price-list record
        if not self.family_quotient:
            pricelist_rec = self.env['product.pricelist'].search(
                [('activate_tco', '=', True), ('no_family_quotient', '=', True)])
        else:
            pricelist_rec = self.env['product.pricelist'].search(
                [('activate_tco', '=', True), ('family_quotient_max', '>=', self.family_quotient),
                 ('family_quotient_min', '<=', self.family_quotient)])
        if len(pricelist_rec) != 1:
            if not pricelist_rec:
                raise exceptions.MissingError(_("No price-list found"))
            else:
                raise exceptions.ValidationError(_("Multiple price-lists found : {ids}").format(ids=pricelist_rec.ids))
        pricelist_rec.ensure_one()

        # get product template record
        product_template_rec = self.env['product.template'].sudo().search(
            [('activate_tco', '=', True), ('tco_transport_titre', '=', self.transport_titre)])
        if len(product_template_rec) != 1:
            if not product_template_rec:
                raise exceptions.MissingError(_("No product template found"))
            else:
                raise exceptions.ValidationError(
                    _("Multiple product template found : {ids}").format(ids=product_template_rec.ids))
        product_template_rec.ensure_one()

        # get product product record
        product_product_rec = self.env['product.product'].sudo().search([
            ('activate_tco', '=', True),
            ('product_tmpl_id', '=', product_template_rec.id),
            ('tco_inscription_invoice_period', '=', self.invoice_period),
            ('tco_inscription_is_derogation', '=', self.is_derogation),
            ('tco_inscription_is_student', '=', self.is_student)])
        if len(product_product_rec) != 1:
            if not product_product_rec:
                raise exceptions.MissingError(_("No product found"))
            else:
                raise exceptions.ValidationError(
                    _("Multiple product found : {ids}").format(ids=product_product_rec.ids))
        product_product_rec.ensure_one()

        # get payment term record
        payment_term_rec = self.env['account.payment.term'].sudo().search([
            ('activate_tco', '=', True),
            ('tco_period_id', '=', self.period_id.id),
            ('tco_inscription_invoice_period', '=', self.invoice_period)])
        if len(payment_term_rec) != 1 and self.invoice_period != 'annually':
            if not payment_term_rec:
                raise exceptions.MissingError(_("No payment term found"))
            else:
                raise exceptions.ValidationError(
                    _("Multiple payment term found : {ids}").format(ids=payment_term_rec.ids))
        # payment_term_rec.ensure_one()

        # Enfant placé par les services sociaux
        partner_invoice_id = self.responsible_id
        if self.is_als and self.als_responsible_id:
            partner_invoice_id = self.als_responsible_id

        # Création du sale order
        sale_order_rec = so_model.sudo().create({'partner_id': self.recipient_id.id,
                                                 'partner_invoice_id': partner_invoice_id.id,
                                                 'partner_shipping_id': self.responsible_id.id,
                                                 'pricelist_id': pricelist_rec.id,
                                                 'payment_term_id': payment_term_rec and payment_term_rec.id or False,
                                                 'date_payment_term_start': self.period_id.date_start,
                                                 'user_id': self.env.user.id,
                                                 })
        # Création du sale order line (rattaché au sale order)
        line_rec = self.env['sale.order.line'].sudo().create({
            'product_id': product_product_rec.id,
            'product_uom_qty': 1,
            'order_id': sale_order_rec.id})

        # On rajoute le nom du bénéficiaire
        # On le fait après la création car le nom de la ligne du SO est un compute.
        line_rec.name = str(self.recipient_id.name) + ": " + line_rec.name
        line_rec._onchange_discount()
        sale_order_rec.action_confirm()

        self.sale_order_ref = sale_order_rec

    # endregion

    # region Model methods
    @api.model
    def get_is_derogation(self, school_establishment_rec, partner_rec):
        """
        Get derofation status depending on partner's location and school establishment sectors.

        :param school_establishment_rec: establishment record
        :param partner_rec: partner record (used to get the street)
        :return: true if partner is in same sector as the establishment, none if the establishment is private
        """
        if not school_establishment_rec.is_public:
            return False
        sector_m = self.env['horanet.school.sector']
        partner_sectors = sector_m.get_sectors(partner_rec.street_id,
                                               partner_rec.street_number_id or None)
        return set(partner_sectors.ids).isdisjoint(school_establishment_rec.school_sector_ids.ids)

    # endregion

    pass
