import logging
import time
from datetime import datetime

from odoo import models, fields, api, _, exceptions

_logger = logging.getLogger(__name__)


class PickupRequest(models.Model):
    """We add some fields."""

    # region Private attributes
    _name = 'environment.pickup.request'
    _inherit = ['mail.thread']
    _order = 'state, schedule_date'

    STATES = [('progress', "In progress"), ('done', "Done")]

    # endregion

    # region Default methods
    @api.model
    def _default_name(self):
        return self.env['ir.sequence'].next_by_code('seq_environment_pickup_request')

    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", default=_default_name, readonly=True)

    emplacement_id = fields.Many2one(
        string="Emplacement",
        comodel_name='stock.emplacement',
        required=True,
    )
    waste_site_id = fields.Many2one(
        string="Waste site",
        comodel_name='environment.waste.site',
        compute='_compute_waste_site',
        store=True,
    )
    activity_id = fields.Many2one(
        string="Activity",
        comodel_name='horanet.activity',
        compute='_compute_activity',
        store=True,
    )
    state = fields.Selection(
        string="State", selection=STATES,
        compute='_compute_state',
        track_visibility='onchange',
        index=True, copy=False,
        readonly=True,
        store=True,
    )
    duration = fields.Float(string="Duration", default=1)
    request_date = fields.Datetime(
        string="Request date",
        default=fields.Datetime.now
    )
    schedule_date = fields.Datetime(
        string="Schedule date",
        default=fields.Datetime.now
    )
    close_date = fields.Datetime(string="Close date", track_visibility='onchange')
    priority = fields.Selection(
        selection=[('0', "Low"), ('1', "Normal"), ('2', "High"), ('3', "Very High")],
        string="Priority",
        default='1',
        help="Set the priority of the request",
    )
    service_provider_id = fields.Many2one(
        string="Service provider",
        comodel_name='res.partner',
        compute='_compute_service_provider_id',
        store=True,
    )
    contract_id = fields.Many2one(
        string="Pickup contract",
        comodel_name='environment.pickup.contract',
        compute='_compute_service_provider_id',
        readonly=True,
        copy=False,
        store=True,
    )
    container_id = fields.Many2one(
        string="Container",
        comodel_name='environment.container',
        compute='_compute_container_id',
        store=True,
    )
    created_by = fields.Char(string="Created by")
    validated_by = fields.Char(string="Validated by")
    filling_level = fields.Integer(string="Filling level", compute='_compute_filling_level', store=True)

    is_provider_notified = fields.Boolean(string="Is provider notified", default=False)

    # endregion

    # region Fields method
    @api.depends('emplacement_id')
    def _compute_filling_level(self):
        for rec in self:
            if rec.emplacement_id:
                rec.filling_level = rec.emplacement_id.filling_level

    @api.depends('emplacement_id')
    def _compute_waste_site(self):
        for rec in self:
            if rec.emplacement_id:
                rec.waste_site_id = rec.emplacement_id.waste_site_id.id

    @api.depends('emplacement_id')
    def _compute_activity(self):
        for rec in self:
            if rec.emplacement_id:
                rec.activity_id = rec.emplacement_id.activity_id.id

    @api.depends('emplacement_id')
    def _compute_service_provider_id(self):
        """We retrieve the service provider by the emplacement's warehouse and waste."""
        pickup_contract_model = self.env['environment.pickup.contract']

        for rec in self:
            contract = pickup_contract_model.search([
                ('waste_site_id', '=', rec.emplacement_id.waste_site_id.id),
                ('activity_ids', '=', rec.emplacement_id.activity_id.id)
            ])

            if len(contract) > 1:
                raise exceptions.ValidationError(
                    _("Service providers: {providers} have a contract to collect this waste.\n"
                      "Please remove this waste from one of those providers contract.").format(
                        providers=', '.join(contract.mapped('service_provider_id.name')))
                )
            if contract:
                rec.service_provider_id = contract.service_provider_id.id
                rec.contract_id = contract.id

    @api.depends('write_date')
    def _compute_state(self):
        """Change the `state` of the pickup request if `close_date` is set."""
        for rec in self:
            if rec.close_date:
                rec.state = 'done'
            else:
                rec.state = 'progress'

    @api.depends('emplacement_id')
    def _compute_container_id(self):
        """Set the `container_id` of the request corresponding to its `emplacement_id`."""
        # Pourquoi sudo ? Parce que sinon si on a pas activer la gestion des bennes et donc le droit de les manager
        # Alors on a une erreur de sécurité
        container_obj = self.env['environment.container'].sudo()

        for rec in self:
            rec.container_id = container_obj.search([
                ('emplacement_id', '=', rec.emplacement_id.id)
            ]).id

    # endregion

    # region Constrains and Onchange
    @api.constrains('state')
    def _check_state_constrains(self):
        u"""Vérifie si la requête peux être modifié en fonction du workflow (state).

        :return: None or raise an exception
        """
        for rec in self:
            list_error_message = []
            if rec.state == 'progress':
                duplicate = self.env['environment.pickup.request'].search_count([
                    ('emplacement_id', '=', rec.emplacement_id.id),
                    ('state', '=', 'progress'),
                    ('id', '!=', rec.id)
                ])
                if duplicate:
                    list_error_message.append(_("A request is still ongoing for this emplacement"))

                if not rec.service_provider_id:
                    list_error_message.append(_("Service provider missing"))
            elif rec.state == 'done':
                if not rec.close_date:
                    list_error_message.append(_("Close date missing"))

            if list_error_message:
                raise exceptions.ValidationError('\n'.join(list_error_message))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_cancel(self, context=None, user_name=None):
        """Cancel a request and notified the provider if necessary.

        Called by Ecopad API

        :param user_name: The string of the person cancelling th request
        :param context: ORM context
        :return: True
        """
        self.ensure_one()
        self.write({
            'close_date': fields.Datetime.now(),
            'validated_by': self.env.user and self.env.user.name or user_name or '---'
        })
        if self.is_provider_notified:
            mail_template = self.env.ref('environment_waste_collect.mail_template_pickup_request_cancel_notification')
            mail_template.send_mail(self.id, force_send=True)

    @api.multi
    def action_close(self, context=None, user_name=None):
        """Cancel a request and notified.

        Called by Ecopad API or backoffice

        :param user_name: The string of the person cancelling the request
        :param context: ORM context
        :return: True
        """
        self.ensure_one()
        self.write({
            'close_date': fields.Datetime.now(),
            'validated_by': self.env.user and self.env.user.name or user_name or '---',
        })
        self.emplacement_id.write({
            'filling_level': 0,
            'last_collect_date': fields.Datetime.now()
        })

    # endregion

    # region Model methods
    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'progress')]

    def _cron_send_pickup_request_mail(self, options=None):
        u"""CRON de génération et d'envoi de mail de relèves de bennes aux prestataire.

        Ce cron permet d'envoyer un mail quotidien de bilan de relèves de bennes (par prestataire)

        :param options:
            `authorized_week_days`: [0, 1, 2, 3, 4, 5]
                jours de la semaine ou le cron peux s'éxécuter, exemple : [0,1] --> que le lundi et le mardi
                par défaut : tout les jours de la semaine.

            `send_zero_request_mail`: <Boolean>
                Si il faut oui ou non envoyer un mail même dans le cas ou il n'y à pas de relèves
        :return:
        """
        week_day_to_send_mail = options and options.get('authorized_week_days', [0, 1, 2, 3, 4, 5, 6])
        send_zero_request_mail = options and options.get('send_zero_request_mail', True)
        if datetime.now().weekday() not in week_day_to_send_mail:
            _logger.info(
                u"Cron : not sending email today. Current weekday ({current_day}) "
                u"not in authorized weekdays ({list_authorized_weekdays}).".format(
                    current_day=unicode(datetime.now().weekday()),
                    list_authorized_weekdays=unicode(week_day_to_send_mail)
                ))
        else:
            service_providers = self.env['res.partner'].search([('is_environment_service_provider', '=', True)])
            if service_providers:
                start_time = time.time()
                _logger.info("Cron : Start sending pickup request mail for {number} service providers".format(
                    number=str(len(service_providers))))
                mail_template = self.with_context(current_time=fields.Datetime.now()).env.ref(
                    'environment_waste_collect.mail_template_summary_pickup_request_notification')

                for provider in service_providers:
                    if not provider.environment_pickup_contract_ids.filtered('is_valid'):
                        # Si le producteur n'a plus de contrat valide -> pas de mail
                        continue
                    if not send_zero_request_mail:
                        if not any([c for c in provider.environment_pickup_contract_ids
                                    if c.active_environment_pickup_request_ids]):
                            continue
                    mail_template.send_mail(provider.id, force_send=True, email_values={'auto_delete': True})
                    requests = provider.mapped('environment_pickup_contract_ids.active_environment_pickup_request_ids')
                    requests.filtered(lambda r: r.state == 'progress' and not r.is_provider_notified).write({
                        'is_provider_notified': True
                    })
                _logger.info(u"Cron : Done sending mail (Total runtime: {exec_time:0.3f}s)".format(
                    exec_time=round(time.time() - start_time, 3)))
            else:
                _logger.info("Cron : No service providers found, this cron could potentially be disabled")

    # endregion
