from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta

from calendar import monthrange
from odoo import models, fields, api, exceptions, _
from ..tools import date_utils

PERIOD_TYPE = [
    ('unlimited', "Unlimited"),
    ('days', "Day(s)"),
    ('weeks', "Week(s)"),
    ('months', "Month(s)"),
    ('years', "Year(s)"),
    ('civil_week', "Civil Week(s)"),
    ('civil_month', "Civil Month(s)"),
    ('civil_year', "Civil Year(s)")
]


class HoranetSubscriptionCycle(models.Model):
    # region Private attributes
    _name = 'horanet.subscription.cycle'
    _sql_constraints = [('unicity', 'UNIQUE(period_type,period_quantity)', _("The cycle must be unique"))]
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", compute='_compute_name', readonly=True)
    period_type = fields.Selection(string="Period type", selection=PERIOD_TYPE, default='unlimited', required=True)
    period_quantity = fields.Integer(string="Quantity")

    # endregion

    # region Fields method
    @api.multi
    @api.depends('period_quantity', 'period_type')
    def _compute_name(self):
        for cycle in self.filtered('period_type'):
            result = self._fields['period_type'].convert_to_export(cycle.period_type, self)

            if cycle.period_type != 'unlimited':
                result = str(cycle.period_quantity) + ' ' + result

            cycle.name = result

    # endregion

    # region Constrains and Onchange
    @api.onchange('period_type')
    def onchange_period_type(self):
        """Pour éviter une erreur de validation, aider l'utilisateur en forçant la quantité quand elle est définie."""
        if self.period_type and self.period_type == 'unlimited':
            self.period_quantity = 0
        if self.period_type and self.period_type in ['civil_week', 'civil_year']:
            self.period_quantity = 1

    @api.constrains('period_type', 'period_quantity')
    def check_values(self):
        """Vérification de la cohérence entre les type et quantités.

        Remarque, il est possible de définir une quantité pour les mois civile (ex: pour faire des trimestres)
        """
        self.ensure_one()
        if self.period_type == 'unlimited' and self.period_quantity != 0:
            raise exceptions.ValidationError(_("The quantity must be null for this type"))
        elif self.period_type in ['civil_week', 'civil_year'] and self.period_quantity != 1:
            raise exceptions.ValidationError(_("The quantity must be set to 1 for this type"))
        elif self.period_type in ['days', 'weeks', 'months', 'years', 'civil_month'] and self.period_quantity <= 0:
            raise exceptions.ValidationError(_("The quantity is mandatory for this cycle"))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.multi
    def get_end_date_of_cycle(self, given_date):
        """Compute a future date from a cycle.

        :param given_date: current date given by the ORM or date/datetime object
        :return: the date in the futur computed from the cycle in the ORM format
        """
        self.ensure_one()

        current_date = date_utils.convert_closing_datetime_to_date(given_date)

        end_date = False

        if self.period_type == 'days':
            end_date = current_date + relativedelta(days=+self.period_quantity - 1)
        if self.period_type == 'weeks':
            end_date = current_date + relativedelta(days=-1, weeks=+self.period_quantity)
        elif self.period_type == 'months':
            end_date = current_date + relativedelta(days=-1, months=+self.period_quantity)
        elif self.period_type == 'years':
            end_date = current_date + relativedelta(days=-1, years=+self.period_quantity)

        elif self.period_type == 'civil_week':
            diff_day = 0

            if current_date.isoweekday() != 7:
                diff_day = 7 - current_date.isoweekday()

            diff_week = self.period_quantity - 1 if self.period_quantity > 0 else 0

            # if today is sunday, we need to add quantity of week to the date
            if not diff_day:
                diff_week = self.period_quantity

            end_date = current_date + relativedelta(days=+diff_day, weeks=diff_week)
        elif self.period_type == 'civil_month':
            last_day_month = monthrange(current_date.year, current_date.month)

            end_date = current_date.replace(day=last_day_month[1],
                                            month=current_date.month + self.period_quantity)
        elif self.period_type == 'civil_year':
            last_day_date = self.get_last_day_date_of_year(
                fields.Date.to_string(current_date)
            )
            last_day_date = fields.Date.from_string(last_day_date)

            end_date = last_day_date

            if self.period_quantity - 1 > 0:
                end_date = last_day_date + relativedelta(years=+self.period_quantity - 1)
        elif self.period_type == 'unlimited':
            return False

        return fields.Date.to_string(end_date)

    @api.multi
    def get_start_date_of_cycle(self, given_date):
        """Get the date of the beginning of a period.

        :param given_date: current date given by the ORM or date/datetime object
        :return: the date in the past computed in the ORM format
        """
        self.ensure_one()

        if self.period_type not in ['civil_week', 'civil_month', 'civil_year']:
            return given_date

        if isinstance(given_date, (datetime, date)):
            current_date = given_date.date()
        elif isinstance(given_date, str):
            current_date = fields.Datetime.from_string(given_date).date()
        else:
            raise ValueError('Expected date/datetime object or str (odoo date) got %s', type(given_date))

        start_date = False

        if self.period_type == 'civil_week':
            start_date = current_date - timedelta(days=current_date.weekday())
        elif self.period_type == 'civil_month':
            current_date = fields.Date.from_string(given_date)
            start_date = current_date.replace(day=1)
        elif self.period_type == 'civil_year':
            current_date = fields.Date.from_string(given_date)
            start_date = current_date.replace(day=1, month=1)

        return fields.Date.to_string(start_date)

    @api.multi
    def get_periods_of_cycle(self, start_date, end_date):
        """Compute periods for a cycle with given dates.

        :param start_date: date given by the ORM or date/datetime object
        :param end_date: date given by the ORM or date/datetime object
        :return: [()] that contains start and end date of each period
        """
        self.ensure_one()
        periods = []

        if start_date > end_date:
            raise ValueError("Bad argument, start_date can't be superior to end_date")

        def _get_next_period(cls, current_compute_date):
            return (
                cls.get_start_date_of_cycle(current_compute_date),
                cls.get_end_date_of_cycle(current_compute_date))

        if start_date == end_date:
            periods.append(_get_next_period(self, start_date))

        while start_date <= end_date:
            periods.append(_get_next_period(self, start_date))
            if not periods[-1][1]:  # Cas d'un cycle illimité
                break
            start_date = fields.Date.from_string(periods[-1][1]) + relativedelta(days=+1)
            start_date = fields.Date.to_string(start_date)

        return periods

    @api.model
    def get_last_day_date_of_year(self, date):
        """Get the date of the last day of the year.

        :param date: date given by the ORM
        :return: the date in the futur computed in the ORM format
        """
        # return datetime.date(fields.Date.from_string(date).year, 12, 31)
        date = fields.Date.from_string(date)

        month_diff = 12 - date.month
        day_diff = 31 - date.day

        last_day_date = date + relativedelta(days=+day_diff, months=+month_diff)

        return fields.Date.to_string(last_day_date)

    @api.model
    def get_next_day_date(self, date):
        """Append one day to date given.

        :param date: date given by the ORM
        :return: the date in the futur computed in the the ORM format
        """
        if not date:
            raise exceptions.UserError(
                _("A date (string) is required, not %s" % date)
            )

        try:
            date = fields.Date.from_string(date)
        except ValueError as e:
            raise exceptions.UserError(e)

        next_day_date = date + relativedelta(days=+1)

        return fields.Date.to_string(next_day_date)

    @api.model
    def get_previous_day_date(self, date):
        """Append one day to date given.

        :param date: date given by the ORM
        :return: the date in the past computed in the the ORM format
        """
        if not date:
            raise exceptions.UserError(
                _("A date (string) is required, not %s" % date)
            )

        try:
            date = fields.Date.from_string(date)
        except ValueError as e:
            raise exceptions.UserError(e)

        next_day_date = date + relativedelta(days=-1)

        return fields.Date.to_string(next_day_date)

    # endregion

    pass
