import logging
import time
from datetime import datetime
from itertools import groupby

try:
    from odoo.addons.mail.models.mail_template import format_tz
except ImportError:
    from mail.models.mail_template import format_tz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Emplacement(models.Model):
    # region Private attributes
    _name = 'stock.emplacement'
    _order = 'filling_level desc'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name")
    activity_id = fields.Many2one(
        string="Waste",
        comodel_name='horanet.activity',
        domain="[('application_type', '=', 'environment')]"
    )
    smarteco_activity_id = fields.Integer(related='activity_id.smarteco_product_id')
    filling_level = fields.Integer(string="Filling level")
    filling_update_date = fields.Datetime(
        string="Filling level last update date",
        compute='_compute_last_update_filling_level',
        readonly=True,
        store=True
    )
    waste_site_id = fields.Many2one(
        string="Waste site",
        comodel_name='environment.waste.site',
        required=True
    )
    smarteco_waste_site_id = fields.Integer(related='waste_site_id.smarteco_waste_site_id')

    code = fields.Char(string="Code", required=True)

    last_collect_date = fields.Datetime(string="Last collect date")

    pickup_request_ids = fields.One2many(
        string="Pickup requests",
        comodel_name='environment.pickup.request',
        inverse_name='emplacement_id'
    )
    pickup_request_count = fields.Integer(
        string="Number of pickup request on this emplacement",
        compute='_compute_pickup_request_count'
    )
    opened_pickup_request = fields.Boolean(
        compute='_compute_pickup_request_count',
        search='_search_opened_pickup_request',
        translate=False
    )
    container_type_id = fields.Many2one(
        string="Container type",
        comodel_name='environment.container.type'
    )

    # endregion

    # region Fields method
    @api.multi
    @api.depends('pickup_request_ids')
    def _compute_pickup_request_count(self):
        """Compute the number of pickup request on each emplacement.

        Also check if one is currently in progress
        """
        for rec in self:
            rec.pickup_request_count = len(rec.pickup_request_ids)
            rec.opened_pickup_request = bool(rec.pickup_request_ids.filtered(
                lambda r: r.state not in ['initial', 'done']
            ))

    @api.multi
    @api.depends('filling_level')
    def _compute_last_update_filling_level(self):
        for rec in self:
            rec.filling_update_date = fields.Datetime.now()

    # endregion

    # region Constrains and Onchange
    @api.multi
    @api.constrains('filling_level')
    def _check_filling_level(self):
        """Check if the filling level is correct (must be set between 0 and 100).

        Doesn't raise an error, the filling level is changed to be valid
        """
        for emplacement in self.filtered(lambda e: not (0 <= e.filling_level <= 100)):
            if emplacement.filling_level < 0:
                emplacement.filling_level = 0
            elif emplacement.filling_level > 100:
                emplacement.filling_level = 100

    @api.multi
    @api.constrains('code')
    def _check_code(self):
        """Check if code is valid.

        :raise: odoo.exceptions.ValidationError if the code is empty
        """
        for rec in self:
            if len(rec.code.strip()) == 0:
                raise ValidationError(_("Code cannot be empty"))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    def _search_opened_pickup_request(self, operator, value):
        """Enable searching on this computed field."""
        if operator == '=':
            emplacements = self.search([
                ('pickup_request_ids', '!=', False),
                ('pickup_request_ids.state', 'not in', ['initial', 'done'])
            ])

        return [('id', 'in', emplacements.ids)]

    def _cron_send_emplacement_filling_level_mail(self, options=None):
        u"""CRON de génération et d'envoi de mail de taux de remplissage des emplacements aux prestataire.

        Ce cron permet d'envoyer un mail (qui peut être quotidien) de bilan de taux de remplissage
        de bennes (par prestataire).

        :param options:
          `authorized_week_days`: <list<int>>, default [0, 1, 2, 3, 4, 5]
              jours de la semaine ou le cron peux s'éxécuter, exemple : [0,1] --> que le lundi et le mardi
              par défaut : tout les jours de la semaine.

          `send_zero_request_mail`: <Boolean>, default = True
              Si il faut oui ou non envoyer un mail même dans le cas ou il n'y à pas d'emplacemenst à afficher

          `minimum_filling_level`: <int>, default = 0
              Valeur limite de remplissage pour afficher l'emplacement dans le mail.
        :return:
        """
        options = options or {}
        week_day_to_send_mail = options and options.get('authorized_week_days', [0, 1, 2, 3, 4, 5, 6])
        send_empty_mail = options and options.get('send_empty_mail', True)
        minimum_filling_level = options and options.get('minimum_filling_level', 0)

        if datetime.now().weekday() not in week_day_to_send_mail:
            _logger.info(
                u"Cron : not sending email today. Current weekday ({current_day}) "
                u"not in authorized weekdays ({list_authorized_weekdays}).".format(
                    current_day=unicode(datetime.now().weekday()),
                    list_authorized_weekdays=unicode(week_day_to_send_mail)
                ))
        else:
            contract_model = self.env['environment.pickup.contract']
            active_contracts = contract_model.search([('is_valid', '=', True)])
            if active_contracts:
                emplacements_by_provider = [
                    (provider, reduce(lambda a, b: a | b, group_contract).mapped('emplacement_ids').filtered(
                        lambda e: e.filling_level >= minimum_filling_level))
                    for provider, group_contract in groupby(active_contracts, lambda p: p.service_provider_id)
                ]

                start_time = time.time()
                _logger.info("Cron : Start sending emplacement filling level {number} service providers".format(
                    number=str(len(emplacements_by_provider))))
                mail_template = self.with_context(current_time=fields.Datetime.now()).env.ref(
                    'environment_waste_collect.mail_template_summary_emplacement_filling_level_notification')

                user_time = fields.Datetime.context_timestamp(self, datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                for provider, emplacements in emplacements_by_provider:
                    # Test pour envoyer le mail si il n'y a pas d'emplacements (empty mail)
                    if not (send_empty_mail or emplacements):
                        continue

                    emplacements_by_wastesite = [
                        (waste_site, reduce(lambda a, b: a | b, group_emplacement))
                        for waste_site, group_emplacement in groupby(emplacements, lambda e: e.waste_site_id)
                    ]
                    mail_template.with_context(
                        emplacements_by_wastesite=emplacements_by_wastesite,
                        minimum_filling_level=minimum_filling_level,
                        user_time=user_time,
                        format_tz=format_tz,
                    ).send_mail(
                        provider.id, force_send=True, email_values={'auto_delete': True})

                _logger.info(u"Cron : Done sending mail (Total runtime: {exec_time:0.3f}s)".format(
                    exec_time=round(time.time() - start_time, 3)))
            else:
                _logger.info("Cron : No service providers found, this cron could potentially be disabled")

    # endregion

    pass
