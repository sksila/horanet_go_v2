from odoo import fields, models, api, exceptions, _
from ..tools import date_utils

try:
    from odoo.addons.horanet_go.tools.utils import format_log
    from odoo.addons.mail.models.mail_template import format_tz, format_date

except ImportError:
    from horanet_go.tools.utils import format_log
    from mail.models.mail_template import format_tz, format_date


class PackageUpdateDate(models.TransientModel):
    # region Private attributes
    _name = 'wizard.package.update.date'

    # endregion

    # region Default methods
    def _default_package_ids(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            packages = self.env['horanet.package'].browse(active_ids)
            return packages
        return False

    # endregion

    # region Fields declaration
    display_form_title = fields.Char(
        string="View form title",
        default=_("Manage packages periods"),
        store=False)

    package_ids = fields.Many2many(
        string="Subscriptions",
        comodel_name='horanet.package',
        default=_default_package_ids,
        readonly=True,
        required=True,
    )
    package_id = fields.Many2one(
        string="Subscription",
        comodel_name='horanet.package',
        compute='_compute_package_id',
        required=False
    )
    is_multiple_update = fields.Boolean(default=True, compute='_compute_is_multiple_update')

    current_opening_date = fields.Char(
        string="Current opening date",
        help="Date at which the package is active",
        related='package_id.display_opening_date')
    current_closing_date = fields.Char(
        string="Current closing date",
        help="Date at which the package is inactive",
        related='package_id.display_closing_date')
    define_new_opening_date = fields.Boolean(string="Define new opening date", default=False)
    define_new_closing_date = fields.Boolean(string="Define new closing date", default=False)
    immediate_closing = fields.Boolean(string="Immediate closing", default=False)
    closing_at_cycle_end = fields.Boolean(string="Close at cycle end", default=False)
    immediate_opening = fields.Boolean(string="Immediate opening", default=False)
    remove_closing_date = fields.Selection(
        string="Remove closing date",
        default='no',
        selection=[('yes', "Yes"), ('no', "No")],
        store=True,
        required=True)
    remove_closing_date = fields.Selection(
        string="Remove closing date",
        default='no',
        selection=[('yes', "Yes"), ('no', "No")],
        store=True,
        required=True)
    new_opening_date = fields.Date(
        string="New opening date",
        help="Date at which the package is active",
        required=False)
    new_closing_date = fields.Date(
        string="New closing date",
        help="Date at which the package is inactive",
        required=False)
    prorata_temporis = fields.Selection(
        string="Apply prorata",
        default='no',
        selection=[('yes', "Yes"), ('no', "No")],
        store=True,
        required=True)
    message_box = fields.Text(
        string="Display message",
        compute='_compute_message_box',
        store=False)

    # endregion

    # region Fields method
    @api.depends('package_ids')
    def _compute_is_multiple_update(self):
        self.ensure_one()
        self.is_multiple_update = len(self.package_ids) > 1

    @api.depends('package_ids')
    def _compute_package_id(self):
        self.ensure_one()
        self.package_id = self.package_ids if len(self.package_ids) == 1 else None

    @api.depends('package_ids')
    def _compute_message_box(self):
        self.ensure_one()
        message = ''

        done_package = self.package_ids.filtered(lambda s: s.state == 'done')
        if done_package:
            message += "<b><error>{title}</error></b>:\n\t{message}\n".format(
                title=_("Warning"),
                message=_(
                    "Some of the selected package are 'done'. The modification of their dates are restricted")
                if len(self.package_ids) > 1 else
                _("The selected package is 'done'. The modifications of it's dates are restricted"))

        self.message_box = message and format_log(message) or False

    # endregion

    # region Constrains and Onchange
    @api.onchange('closing_at_cycle_end')
    def _onchange_closing_at_cycle_end(self):
        self.ensure_one()
        if self.closing_at_cycle_end:
            self.immediate_closing = False

    @api.onchange('immediate_closing')
    def _onchange_immediate_closing(self):
        self.ensure_one()
        if self.immediate_closing:
            self.closing_at_cycle_end = False

    @api.onchange('define_new_closing_date')
    def _onchange_define_new_closing_date(self):
        self.ensure_one()
        if self.define_new_closing_date:
            self.remove_closing_date = 'no'

    @api.onchange('remove_closing_date')
    def _onchange_remove_closing_date(self):
        self.ensure_one()
        if self.remove_closing_date == 'yes':
            self.define_new_closing_date = False

    @api.constrains('new_opening_date', 'new_closing_date', 'package_ids', 'remove_closing_date',
                    'define_new_opening_date', 'define_new_closing_date', 'immediate_opening', 'immediate_closing')
    def _check_date_consistency(self):  # noqa: D401
        """Validation technique des paramètres demandés."""
        self.ensure_one()
        if self.remove_closing_date == 'yes' and self.define_new_opening_date:
            raise exceptions.ValidationError("Can't remove AND define closing date at the same time")

        if self.define_new_opening_date and self.define_new_closing_date:
            if self.immediate_closing:
                new_date_opening = fields.Datetime.now()
            else:
                if not self.new_opening_date:
                    raise exceptions.ValidationError("New opening date must be set")
                new_date_opening = fields.Datetime.from_string(self.new_opening_date)

            if not self.closing_at_cycle_end:
                if self.immediate_closing:
                    new_date_closing = fields.Datetime.now()
                else:
                    if not self.new_closing_date:
                        raise exceptions.ValidationError("New closing date must be set")
                    new_date_closing = date_utils.convert_date_to_closing_datetime(self.new_closing_date)

                if new_date_closing < new_date_opening:
                    raise exceptions.ValidationError(_(
                        "New ending date should be posterior or equal to opening date."))

    @api.constrains()
    def _validate_all(self):  # noqa: D401
        """Valide l'aspect fonctionnel du paramétrage demandé."""
        if not self.define_new_opening_date \
                and not self.define_new_closing_date \
                and self.remove_closing_date != 'yes' \
                and self.prorata_temporis != 'yes':
            raise exceptions.ValidationError(_("Nothing to do, use the cancel button or select a parameter to update"))

        if self.remove_closing_date == 'yes' or self.define_new_opening_date or self.define_new_closing_date:
            done_packages = self.package_ids.filtered(lambda s: s.state == 'done')
            if done_packages:
                # Dans le cas ou il n'y à qu'un abonnement de sélectionné
                if self.package_id:
                    raise exceptions.ValidationError(
                        _("The selected package is 'done'. The modifications of it's dates are restricted"))
                else:
                    raise exceptions.ValidationError(
                        _("""Certain ({number}) of the selected packages are 'done'.
                         The modifications of their dates are restricted""").format(
                            number=str(len(done_packages))))

        # Vérification de la saisie d'une date d'ouverture sur les packages draft
        if not self.define_new_opening_date:
            draft_packages = self.package_ids.filtered(lambda s: not s.opening_date)
            if draft_packages:
                # Dans le cas ou il n'y à qu'un abonnement de sélectionné
                if self.package_id:
                    raise exceptions.ValidationError(
                        _("The selected package is 'draft'. An opening date must be specified"))
                else:
                    raise exceptions.ValidationError(
                        _("""Certain ({number}) of the selected packages are 'draft'.
                         An opening date must be specified""").format(
                            number=str(len(draft_packages))))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    def action_update_date(self):
        self.ensure_one()
        # Appel de la validation des data (c'est ces méthodes qui doivent gérer les cas d'erreur)
        self._check_date_consistency()
        self._validate_all()

        # Définir les éventuelles nouvelles dates de fin

        new_opening_date = None
        if self.define_new_opening_date:
            new_opening_date = fields.Datetime.now() if self.immediate_opening else self.new_opening_date

        new_closing_date = None
        if self.remove_closing_date != 'yes' and self.define_new_closing_date:
            if self.closing_at_cycle_end:
                # La méthode du calcul de ligne ajoutera automatiquement
                # la nouvelle date de fin a la date du dernier cycle
                self.package_ids.write({'is_renewable': True})
            new_closing_date = fields.Datetime.now() if self.immediate_closing else self.new_closing_date

        # La méthode du calcul de ligne ajoutera automatiquement la nouvelle date de fin a la date du dernier cycle
        if self.remove_closing_date == 'yes':
            self.package_ids.write({'is_renewable': True})

        # Création d'un message custom pour tracer les modification d'objet effectué depuis ce wizard
        track_message = self._generate_message_update_date(new_opening_date, new_closing_date)
        if track_message:
            for package in self.package_ids:
                package.message_post(body=track_message, message_type='comment', subtype='mail.mt_note')

        self.package_ids.update_active_period(
            opening_date=new_opening_date,
            closing_date=new_closing_date,
            prorata=self.prorata_temporis,
            remove_closing_date=self.remove_closing_date == 'yes',
        )

    def _generate_message_update_date(self, new_opening_date, new_closing_date):
        """Génère un message en fonction des paramètres sélectionné dans le wizard.

        Ne dois être appelé qu'après validation des paramètres technique/fonctionnel
        :param new_opening_date: L'éventuelle nouvelle date d'ouverture
        :param new_closing_date: L'éventuelle nouvelle date de fermeture
        :return: Une chaîne HTML contenant le résumé de l'opération du wizard
        """
        track_message = '<b>' + _("Date update:") + '</b>\t'
        if len(self.package_ids) == 1:
            track_message += '<i>' + _("On this record only (code {package_code})").format(
                package_code=str(self.package_ids[0].code)) + '</i>'
        else:
            max_length = 80
            list_id = ','.join([str(s_id) for s_id in self.package_ids.ids])
            if len(list_id) > max_length and list_id[:max_length].rfind(','):
                list_id = list_id[:list_id[:max_length].rfind(',')] + ' ...'
            track_message += '<i>' + _("On {record_number} packages (id : {first_id_in_list})").format(
                record_number=str(len(self.package_ids)),
                first_id_in_list=list_id) + '</i>'
        track_message += '\n' + _("Operation: ")
        operation_detail = ''
        if new_opening_date:
            if self.immediate_opening:
                operation_detail += '\n\t- ' + _("New opening date (immediate opening): {opening_date}.").format(
                    opening_date=format_tz(self.env, new_opening_date))
            else:
                operation_detail += '\n\t- ' + _("New opening date: {opening_date}.").format(
                    opening_date=format_date(self.env, new_opening_date))
        if new_closing_date:
            if self.immediate_closing:
                operation_detail += '\n\t- ' + _("New closing date (immediate closing): {closing_date}.").format(
                    closing_date=format_tz(self.env, new_closing_date))
            else:
                operation_detail += '\n\t- ' + _("New closing date: {closing_date}.").format(
                    closing_date=format_date(self.env, new_closing_date))
        elif self.closing_at_cycle_end:
            operation_detail += '\n\t- ' + _("New closing date set at cycle end.")
        if self.remove_closing_date == 'yes':
            operation_detail += '\n\t- ' + _("Remove closing date.")

        if self.prorata_temporis == 'yes':
            operation_detail += ' ' + _("And update prorata.") if operation_detail else '\n\t- ' + _("Update prorata.")
        elif operation_detail:
            operation_detail += ' ' + _("Without update prorata.")

        track_message += operation_detail
        track_message = format_log(track_message)

        return track_message

    # endregion

    # region Model methods

    # endregion

    pass
