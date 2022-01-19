
from odoo import fields, models, api, exceptions, _
from odoo.tools import safe_eval

import pytz
import werkzeug
import datetime


def urlplus(url, params):
    return werkzeug.Href(url)(params or None)


class WasteSite(models.Model):
    # region Private attributes
    _name = 'environment.waste.site'
    _inherits = {'horanet.infrastructure': 'infrastructure_id'}

    # endregion

    # region Default methods
    @api.model
    def _tz_get(self):
        # put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
        return [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]

    # endregion

    # region Fields declaration
    infrastructure_id = fields.Many2one(comodel_name='horanet.infrastructure', required=True, ondelete='cascade')

    smarteco_waste_site_id = fields.Integer(string="SmartEco Waste Site ID")

    partner_guardian_ids = fields.Many2many(string="Guardians", compute='_compute_partner_guardian_ids',
                                            comodel_name='res.partner', store=False)

    phone = fields.Char(string="Phone")
    image = fields.Binary(string="Image")
    email = fields.Char(
        string="Email",
        help="Required to be able to receive sent pickup requests",
        required=True
    )

    is_attendance_controlled = fields.Boolean(
        string="Control attendance",
        default=False)
    attendance_threshold = fields.Integer(
        string="Attendance threshold",
        default=10)
    current_attendance = fields.Integer(
        string="Current attendance",
        compute='compute_current_attendance',
        store=False)
    could_attend = fields.Boolean(
        string="Can attend",
        compute='compute_could_attend',
        store=False)

    control_timetable = fields.Boolean(string="Control timetable", default=False)
    timezone = fields.Selection(string="Timezone", selection=_tz_get,
                                default=lambda self: self._context.get('tz'))
    date_winter = fields.Date(string="Winter date")
    date_summer = fields.Date(string="Summer date")
    monday_opening_hour = fields.Float(string="Monday opening hour", default=8)
    monday_closing_hour = fields.Float(string="Monday closing hour", default=19)
    tuesday_opening_hour = fields.Float(string="Tuesday opening hour", default=8)
    tuesday_closing_hour = fields.Float(string="Tuesday closing hour", default=19)
    wednesday_opening_hour = fields.Float(string="Wednesday opening hour", default=8)
    wednesday_closing_hour = fields.Float(string="Wednesday closing hour", default=19)
    thursday_opening_hour = fields.Float(string="Thursday opening hour", default=8)
    thursday_closing_hour = fields.Float(string="Thursday closing hour", default=19)
    friday_opening_hour = fields.Float(string="Friday opening hour", default=8)
    friday_closing_hour = fields.Float(string="Friday closing hour", default=19)
    saturday_opening_hour = fields.Float(string="Saturday opening hour", default=8)
    saturday_closing_hour = fields.Float(string="Saturday closing hour", default=19)
    winter_monday_opening_hour = fields.Float(string="Winter monday opening hour", default=8)
    winter_monday_closing_hour = fields.Float(string="Winter monday closing hour", default=19)
    winter_tuesday_opening_hour = fields.Float(string="Winter tuesday opening hour", default=8)
    winter_tuesday_closing_hour = fields.Float(string="Winter tuesday closing hour", default=19)
    winter_wednesday_opening_hour = fields.Float(string="Winter wednesday opening hour", default=8)
    winter_wednesday_closing_hour = fields.Float(string="Winter wednesday closing hour", default=19)
    winter_thursday_opening_hour = fields.Float(string="Winter thursday opening hour", default=8)
    winter_thursday_closing_hour = fields.Float(string="Winter thursday closing hour", default=19)
    winter_friday_opening_hour = fields.Float(string="Winter friday opening hour", default=8)
    winter_friday_closing_hour = fields.Float(string="Winter friday closing hour", default=19)
    winter_saturday_opening_hour = fields.Float(string="Winter saturday opening hour", default=8)
    winter_saturday_closing_hour = fields.Float(string="Winter saturday closing hour", default=19)

    deposit_activity_sector_id = fields.Many2one(
        string="Deposit activity sector",
        comodel_name='activity.sector',
        store=True,
    )
    deposit_check_point_id = fields.Many2one(
        string="Deposit check point",
        comodel_name='device.check.point',
        help="Not intended to display, used to cleanup old checkpoint in "
             "case of change of 'deposit_activity_sector_id'",
        readonly=True)

    served_city_ids = fields.Many2many(
        string="Served cities",
        comodel_name='res.city')

    terminal_ids = fields.Many2many(
        string="Terminals",
        comodel_name='device.check.point',
        compute='_compute_terminal_ids',
        inverse='inverse_terminals_ids',
        store=False,
        readonly=False)

    is_linked_to_smarteco = fields.Boolean(compute='_get_is_linked_to_smarteco', store=False)

    # endregion

    # region Fields method
    @api.depends('infrastructure_id')
    def _compute_terminal_ids(self):
        """Get a filtered list of waste_site checkpoints (only terminals == no device)."""
        for ws in self:
            ws.terminal_ids = ws.infrastructure_id.check_point_ids.filtered('device_id')

    @api.multi
    def inverse_terminals_ids(self):
        u"""Déclenché au changement des terminaux, sert à gérer le déférencement/référencement.

         la création d'un nouveau terminal de déchetterie est géré via le context et une surcharge de la
         méthode :meth:`odoo.addons.environment_waste_collect.models.DeviceCheckPointIP.create` du check_point

        :return: nothing
        """
        for ws in self:
            new_terminals = self.env['device.check.point']
            old_checkpoints = ws.infrastructure_id.check_point_ids
            for cp in ws.terminal_ids - old_checkpoints:
                # fonctionne car le check_point n'a pas de champ m2m stocké, erreur sinon
                vals = {k: cp[k].id or False if hasattr(cp[k], 'id') else cp[k] for k in cp.copy_data()[0].keys()}
                # force infrastructure (should be hidden in view)
                vals.update({'infrastructure_id': self.id, 'device_unique_id': cp.device_unique_id})
                new_terminals += cp.with_context(auto_manage_terminal=True).create(vals)
            # TODO: il ne faudrait jamais supprimer un CP, car il peux être référencé par une opération
            check_point_to_unlink = old_checkpoints.filtered('device_id') - ws.terminal_ids - new_terminals
            check_point_to_unlink.unlink()

    @api.depends('attendance_threshold', 'current_attendance', 'is_attendance_controlled')
    def compute_could_attend(self):
        for rec in self:
            rec.could_attend = self.can_attend()

    @api.depends('attendance_threshold')
    def compute_current_attendance(self):
        for waste_site in self:
            waste_site.current_attendance = self.get_current_attendance()

    @api.depends()
    def _compute_partner_guardian_ids(self):
        partner_model = self.env['res.partner']
        guardian_cate = self.env.ref('environment_waste_collect.environment_category_guardian')
        guardians = partner_model.search([('subscription_category_ids', 'in', guardian_cate)])
        for waste_site in self:
            waste_site.partner_guardian_ids = guardians

    @api.depends()
    def _get_is_linked_to_smarteco(self):
        """Return the environment setting."""
        is_linked_to_smarteco_config = safe_eval(
            self.env['ir.config_parameter'].get_param('environment_waste_collect.is_linked_to_smarteco', 'False')
        )
        for waste_site in self:
            waste_site.is_linked_to_smarteco = is_linked_to_smarteco_config

    # region Constrains and Onchange
    @api.onchange('is_attendance_controlled', 'attendance_threshold')
    def onchange_attendance_controlled(self):
        u"""Control de la validité des données pour informer l'utilisateur avant l'enregistrement.

        Prévenir l'utilisateur si le control de FMI est activé, mais limité à zero personnes (bloque le site)
        """
        self.ensure_one()
        if self.is_attendance_controlled and not self.attendance_threshold:
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _("The attendance control is enabled, but the threshold is set to 0 !")
                }
            }

    @api.constrains('control_timetable', 'monday_opening_hour', 'monday_closing_hour', 'tuesday_opening_hour',
                    'tuesday_closing_hour', 'wednesday_opening_hour', 'wednesday_closing_hour', 'thursday_opening_hour',
                    'thursday_closing_hour', 'friday_opening_hour', 'friday_closing_hour', 'winter_monday_opening_hour',
                    'winter_monday_closing_hour', 'winter_tuesday_opening_hour', 'winter_tuesday_closing_hour',
                    'winter_wednesday_opening_hour', 'winter_wednesday_closing_hour', 'winter_thursday_opening_hour',
                    'winter_thursday_closing_hour', 'winter_friday_opening_hour', 'winter_friday_closing_hour',
                    'winter_saturday_opening_hour', 'winter_saturday_closing_hour', 'date_summer', 'date_winter')
    def check_timetable_value(self):
        """Check the consistency of timetable hour.

        :return: nothing
        :raise: Validation error if opening hour superior to closing hour
        """
        for ws in self:
            if ws.control_timetable:
                if ws.monday_opening_hour > ws.monday_closing_hour \
                        or ws.tuesday_opening_hour > ws.tuesday_closing_hour \
                        or ws.wednesday_opening_hour > ws.wednesday_closing_hour \
                        or ws.thursday_opening_hour > ws.thursday_closing_hour \
                        or ws.friday_opening_hour > ws.friday_closing_hour \
                        or ws.saturday_opening_hour > ws.saturday_closing_hour \
                        or ws.winter_monday_opening_hour > ws.winter_monday_closing_hour \
                        or ws.winter_tuesday_opening_hour > ws.winter_tuesday_closing_hour \
                        or ws.winter_wednesday_opening_hour > ws.winter_wednesday_closing_hour \
                        or ws.winter_thursday_opening_hour > ws.winter_thursday_closing_hour \
                        or ws.winter_friday_opening_hour > ws.winter_friday_closing_hour \
                        or ws.winter_saturday_opening_hour > ws.winter_saturday_closing_hour:
                    raise exceptions.ValidationError(_("Opening hour must be inferior to closing hour"))
                if not ws.date_winter:
                    raise exceptions.ValidationError(_("Winter date must be set"))
                if not ws.date_summer:
                    raise exceptions.ValidationError(_("Summer date must be set"))
                day_summer = fields.Date.from_string(ws.date_summer).timetuple().tm_yday
                day_winter = fields.Date.from_string(ws.date_winter).timetuple().tm_yday

                if day_winter < day_summer:
                    raise exceptions.ValidationError(_("Winter day must be superior to summer day"))

    # endregion

    # region CRUD (overrides)
    @api.model
    def create(self, vals):
        """
        Override to create a 'deposit' check-point if necessary.

        If the waste site has the attribute 'deposit_activity_sector_id', a checkpoint will be created to
        associate the waste-site with the activity sector, this will be a check-point without device.
        """
        new_waste_site = super(WasteSite, self).create(vals)
        if new_waste_site.deposit_activity_sector_id:
            deposit_check_point_id = self.env['device.check.point'].sudo().create({
                'name': _("Auto generated for {waste_site_name} / {sector_name}").format(
                    waste_site_name=new_waste_site.name,
                    sector_name=new_waste_site.deposit_activity_sector_id.name),
                'input_activity_sector_id': new_waste_site.deposit_activity_sector_id.id,
                'infrastructure_id': new_waste_site.infrastructure_id.id,
            })
            # write triggered after create, sale, mais requis car le checkpoint est liée à l'objet fraîchement créée
            new_waste_site.deposit_check_point_id = deposit_check_point_id

        return new_waste_site

    @api.multi
    def write(self, vals):
        """
        Override to update a 'deposit' check-point if necessary.

        If the waste site has the attribute 'deposit_activity_sector_id' and there is no checkpoint associating
        the waste-site with the activity sector, a check point will be created and previous checkpoint will be
        deleted.
        """
        if 'deposit_activity_sector_id' in vals:
            activity_sector = vals.get('deposit_activity_sector_id', False) \
                              and self.env['activity.sector'].sudo().browse(vals['deposit_activity_sector_id']) \
                              or None
            for waste_site in self:
                # Si un nouveau secteur d'activité de waste_site est défini,
                # créer ou mettre à jour le checkpoint de dépôt (automatiquement défini)
                if activity_sector:
                    cp_vals = {
                        'name': _("Auto generated for {waste_site_name} / {sector_name}").format(
                            waste_site_name=waste_site.name,
                            sector_name=activity_sector.name),
                        'input_activity_sector_id': activity_sector.id,
                        'infrastructure_id': waste_site.infrastructure_id.id}
                    if waste_site.deposit_check_point_id:
                        waste_site.deposit_check_point_id.write(cp_vals)
                    else:
                        waste_site.deposit_check_point_id = self.env['device.check.point'].sudo().create(cp_vals)

                # Cas ou on supprime la zone d'activité de dépôt du waste site,
                # supprimer l'eventuel check point de dépôt (automatiquement défini)
                elif waste_site.deposit_check_point_id:
                    # TODO : à terme il ne faudrait jamais supprimer un checkpoint, juste le désactiver
                    waste_site.deposit_check_point_id.unlink()

        return super(WasteSite, self).write(vals)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_current_attendance(self):
        self.ensure_one()
        current_attendance = 0
        relevant_operations = self._get_relevant_fmi_operations()
        if relevant_operations:
            for operation in relevant_operations.sorted('time', reverse=True):
                if operation.action_id.code == 'CALIBRATE_FMI':
                    current_attendance += operation.quantity
                    break
                elif operation.action_id.code == 'PASS':
                    current_attendance += operation.quantity
                elif operation.action_id.code == 'EXIT':
                    current_attendance -= operation.quantity

        return current_attendance

    @api.multi
    def can_attend(self):
        self.ensure_one()
        can_attend = True
        if self.is_fmi_control_enable():
            can_attend = self.attendance_threshold > self.get_current_attendance()

        return can_attend

    @api.multi
    def is_fmi_control_enable(self):
        is_fmi_enable = False
        if self.is_attendance_controlled:
            control_fmi_operations = self._get_relevant_fmi_operations().filtered(
                lambda o: o.action_id.code in ['ENABLE_FMI', 'DISABLE_FMI'])
            if control_fmi_operations:
                last_control_operation = control_fmi_operations.sorted('time', reverse=True)[0]
                if last_control_operation.action_id.code == 'DISABLE_FMI':
                    is_fmi_enable = False
                elif last_control_operation.action_id.code == 'ENABLE_FMI':
                    is_fmi_enable = True
            else:
                is_fmi_enable = True
        return is_fmi_enable

    @api.multi
    def _get_relevant_fmi_operations(self):
        relevant_actions = self.env['horanet.action'].sudo().search([
            ('code', 'in', ['CALIBRATE_FMI', 'ENABLE_FMI', 'DISABLE_FMI', 'EXIT', 'PASS'])])
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        relevant_operations = self.env['horanet.operation'].sudo().search([
            ('time', '>=', str(today)), ('time', '<', str(tomorrow)),
            ('infrastructure_id', '=', self.infrastructure_id.id), ('action_id', 'in', relevant_actions.ids)])
        return relevant_operations

    @api.multi
    def is_open_hour(self):
        self.ensure_one()
        is_open = True
        if self.control_timetable:
            timezone = pytz.timezone(self.timezone or self.write_uid.tz)
            now = datetime.datetime.now().replace(tzinfo=pytz.UTC).astimezone(timezone)
            summer_date = fields.Date.from_string(self.date_summer)
            winter_date = fields.Date.from_string(self.date_winter)
            is_summer = summer_date.timetuple().tm_yday <= now.timetuple().tm_yday < winter_date.timetuple().tm_yday
            day_idx = now.isoweekday()
            hour = now.hour + now.minute / 60. + now.second / 3600.
            if is_summer:
                if day_idx == 1:
                    is_open = self.monday_opening_hour <= hour <= self.monday_closing_hour
                if day_idx == 2:
                    is_open = self.tuesday_opening_hour <= hour <= self.tuesday_closing_hour
                if day_idx == 3:
                    is_open = self.wednesday_opening_hour <= hour <= self.wednesday_closing_hour
                if day_idx == 4:
                    is_open = self.thursday_opening_hour <= hour <= self.thursday_closing_hour
                if day_idx == 5:
                    is_open = self.friday_opening_hour <= hour <= self.friday_closing_hour
                if day_idx == 6:
                    is_open = self.saturday_opening_hour <= hour <= self.saturday_closing_hour
            else:
                if day_idx == 1:
                    is_open = self.winter_monday_opening_hour <= hour <= self.winter_monday_closing_hour
                if day_idx == 2:
                    is_open = self.winter_tuesday_opening_hour <= hour <= self.winter_tuesday_closing_hour
                if day_idx == 3:
                    is_open = self.winter_wednesday_opening_hour <= hour <= self.winter_wednesday_closing_hour
                if day_idx == 4:
                    is_open = self.winter_thursday_opening_hour <= hour <= self.winter_thursday_closing_hour
                if day_idx == 5:
                    is_open = self.winter_friday_opening_hour <= hour <= self.winter_friday_closing_hour
                if day_idx == 6:
                    is_open = self.winter_saturday_opening_hour <= hour <= self.winter_saturday_closing_hour
        return is_open

    # endregion

    pass
