from datetime import datetime

from odoo import models, fields, api
from odoo.osv import expression
from ..config import config
from ..tools import date_utils

try:
    from odoo.addons.mail.models.mail_template import format_tz, format_date
except ImportError:
    from mail.models.mail_template import format_tz, format_date


class SubscriptionShared(models.AbstractModel):
    """Classe commune au quatres modèles de gestion des abonnements.

    - horanet.subscription
    - horanet.subscription.line
    - horanet.package
    - horanet.package.line
    **Remarque**: Certaines méthode ne sont disponible que pour certains des quatres modèles
    """

    # region Private attributes
    _name = 'horanet.subscription.shared'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    display_opening_date = fields.Char(
        string="Opening date",
        help="Date at which the subscription is active",
        readonly=True,
        compute='get_display_opening_date')
    display_closing_date = fields.Char(
        string="Closing date",
        help="Date at which the subscription is inactive",
        readonly=True,
        compute='get_display_closing_date')
    display_progress_period = fields.Integer(
        string="Current period",
        compute='_compute_display_progress_period',
        store=False)
    state = fields.Selection(
        string="State",
        selection=config.SUBSCRIPTION_STATE,
        compute='_compute_state',
        search='_search_state')

    # endregion

    # region Fields method
    @api.depends('opening_date')
    def get_display_opening_date(self):
        """Objectif : afficher la composante horaire uniquement si l'utilisateur l'a définie.

        Comme les dates sont dans un référentiel UTC, pour simplifier l'interface utilisateur, n'afficher
        que la composante date de l'instant d'ouverture de l'abonnement. Pour cela, il faut vérifier
        que la datetime d'ouverture n'a pas de composante horaire.

        exemple : 01/01/2019 00:00:00 équivaut à 31/12/2018
        """
        for rec in self:
            result = '---'
            if rec.opening_date:
                if not fields.Datetime.from_string(rec.opening_date).time():
                    result = format_date(self.env, rec.opening_date)
                else:
                    result = format_tz(self.env, rec.opening_date)

            rec.display_opening_date = result

    @api.depends('closing_date')
    def get_display_closing_date(self):
        """Objectif : afficher la composante horaire uniquement si l'utilisateur l'a définie.

        Comme les dates sont dans un référentiel UTC, pour simplifier l'interface utilisateur, n'afficher
        que la composante date de l'instant de fermeture de l'abonnement. Pour cela, il faut vérifier
        que la datetime de clôture n'a pas de composante horaire.

        exemple : 01/01/2019 00:00:00 équivaut à 31/12/2018
        """
        for rec in self:
            result = '---'
            if rec.closing_date:
                if not fields.Datetime.from_string(rec.closing_date).time():
                    # Afficher uniquement la composante date
                    closing_date = date_utils.convert_closing_datetime_to_date(rec.closing_date)
                    result = format_date(self.env, fields.Date.to_string(closing_date))
                else:
                    result = format_tz(self.env, rec.closing_date)

            rec.display_closing_date = result

    @api.depends()
    def _compute_display_progress_period(self):
        """Compute the period as percent based on the current date, for display purpose."""
        date_now = fields.Datetime.now()
        datetime_now = datetime.now()
        for rec in self:
            result = 0
            if not rec.closing_date:
                if rec.opening_date < date_now:
                    result = 50
                else:
                    result = 0
            elif rec.closing_date <= date_now:
                result = 100
            elif rec.opening_date > date_now:
                result = 0
            elif rec.opening_date <= date_now < rec.closing_date:
                theoretical_period = (
                    fields.Datetime.from_string(rec.opening_date),
                    fields.Datetime.from_string(rec.closing_date))
                duration_theoretical = (theoretical_period[1] - theoretical_period[0]).total_seconds()
                duration_practical = (datetime_now - theoretical_period[0]).total_seconds()
                result = min(max(abs(int((duration_practical / duration_theoretical) * 100)), 10), 90)

            rec.display_progress_period = result

    def _get_compute_state_depends(self):
        depends_fields = ['start_date', 'end_date', 'opening_date', 'closing_date']
        if self._name in ['horanet_subscription']:
            depends_fields.append('confirmation_date')
        return depends_fields

    @api.depends(lambda self: self._get_compute_state_depends())
    def _compute_state(self):
        """Compute the state of the package.

        State is computed via the different dates, as explained below :

        **Attention the confirmation_date exist only for subscription record**. If no confirmation date --> draft

        Table if closing_date is set:

        | .. pending   | pending  |       active       |    closed    | done ..
        | -------------|----------|--------------------|--------------|--------> t
        |             S_D        O_D                  C_D            E_D

        Table if closing_date is not set:

        | .. pending   | pending  |              active              |  to_compute ..
        | -------------|----------|----------------------------------|--------------> t
        |             S_D        O_D                                E_D

        If no start_date (only for subscription and package) --> draft
        """
        search_date = fields.Date.context_today(self)  # Local
        search_date_time = fields.Datetime.now()  # UTC

        for rec in self:
            state = 'to_compute'
            if rec._name in ['horanet_subscription'] and not rec.confirmation_date:
                state = 'draft'
            elif not rec.opening_date:
                state = 'draft'

            elif rec.opening_date and not rec.start_date:
                state = 'to_compute'
            elif rec.opening_date and rec.start_date <= search_date and not rec.end_date:
                state = 'to_compute'
            elif rec.closing_date and not rec.end_date:
                state = 'to_compute'
            elif not rec.closing_date and rec.end_date < search_date:
                state = 'to_compute'

            elif rec.opening_date > search_date_time:
                state = 'pending'
            elif rec.start_date and rec.opening_date < search_date_time and \
                    (not rec.closing_date or rec.closing_date > search_date_time):
                state = 'active'

            elif rec.closing_date and rec.end_date \
                    and rec.closing_date < search_date_time and rec.end_date >= search_date:
                state = 'closed'

            elif rec.closing_date and rec.end_date and rec.end_date < search_date:
                state = 'done'

            rec.state = state

    def _search_state(self, operator, value, search_date_utc=False):
        """Return a domain to be able to search subscriptions with their states.

        **Attention the confirmation_date exist only for subscription record**. If no confirmation date --> draft

        Table if closing_date is set:

        | .. pending   | pending  |       active       |    closed    | done ..
        | -------------|----------|--------------------|--------------|--------> t
        |             S_D        O_D                  C_D            E_D

        Table if closing_date is not set:

        | .. pending   | pending  |              active              |  to_compute ..
        | -------------|----------|----------------------------------|--------------> t
        |             S_D        O_D                                E_D

        If no start_date (only for subscription and package) --> draft

        :param operator: search operator (only '=' or '!=')
        :param value: searched value
        :return: a domain that filters on the dates
        """
        if isinstance(value, (list, tuple)):
            raise NotImplementedError('Cannot search on multiple states at the same time')
        if operator not in ['=', '!=']:
            raise ValueError("Got operator '%s' (expected '=' or '!=')" % operator)

        # Détermination de la date contextuelle (en cas d'appel via les règles d'activité)
        search_date_time = search_date_utc or self.env.context.get('force_time', fields.Datetime.now())
        search_date = fields.Date.from_string(search_date_time)  # UTC

        domain = []

        # Création du domaine en logique positive (recherche avec opérateur '=')
        if value == 'draft':
            if self._name in ['horanet_subscription']:
                domain = [('confirmation_date', '=', False)]
            domain = expression.OR([domain, [('opening_date', '=', False)]])

        elif value == 'pending':
            domain = expression.AND([
                [('opening_date', '!=', False)],
                [('opening_date', '>', search_date_time)]
            ])

        elif value == 'active':
            domain = expression.AND([
                [('opening_date', '!=', False)],
                [('opening_date', '<=', search_date_time)],
                expression.OR([
                    [('closing_date', '=', False)],
                    [('closing_date', '>', search_date_time)]
                ])
            ])

        elif value == 'closed':
            domain = expression.AND([
                [('closing_date', '!=', False)],
                [('end_date', '!=', False)],
                [('closing_date', '<', search_date_time)],
                [('end_date', '>=', search_date)]
            ])

        elif value == 'done':
            domain = expression.AND([
                [('closing_date', '!=', False)],
                [('end_date', '!=', False)],
                [('end_date', '<', search_date)]
            ])

        # to_compute représente tout les état dont il manque une période ou un composant de date
        elif value == 'to_compute':
            domain = \
                expression.OR([
                    expression.AND([
                        [('opening_date', '!=', False)],
                        [('start_date', '=', False)]]),
                    expression.AND([
                        [('opening_date', '!=', False)],
                        [('start_date', '<=', search_date)],
                        [('end_date', '=', False)]]),
                    expression.AND([
                        [('closing_date', '!=', False)],
                        [('end_date', '=', False)]]),
                    expression.AND([
                        [('closing_date', '=', False)],
                        [('end_date', '<', search_date)]])
                ])

        # Gestion du cas particulier du modèle horanet.subscription qui possède une date de confirmation,
        # qui fait partie du calcul de l'état
        if self._name in ['horanet_subscription']:
            if value == 'draft':
                domain = expression.AND([[('confirmation_date', '=', False)], domain])
            else:
                domain = expression.AND([[('confirmation_date', '!=', False)], domain])

        # Négation du domaine ne cas de recherche négative
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain.insert(0, expression.NOT_OPERATOR)

        return expression.normalize_domain(domain)

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods

    @api.multi  # noqa: C901 - Garder une méthode pour faciliter la lecture
    def _compute_object_line(self, compute_date=None):
        """Création et mise à jour des lignes, à une éventuelle date.

        Remaque: Cette méthode est appelée par les abonnement ainsi que les forfaits (subscription and package).

        Basé sur les information du cycle du modèle et ses dates d'ouverture/clôture, cette méthode
        créé les lignes ou les mets à jour.

        En cas de changement de cycle, le nouveau cycle ne correspondant pas à l'ancien, un problème peux
        exister lors du calcul des lignes. Le principe de base est 'ne pas réduire une ligne existante', car les
        ligne portent les usages et la facturation, réduire une ligne c'est s'exposer à des incohérences de liaison
        par date des usages et sale.order.line / sale.order.
        Les période sont donc étendues, sauf dans le cas ou la période à étendre n'est pas comprise dans le
        nouveau cycle théorique

        :param compute_date: Date ORM, Sert de limite de calcul dans le cas d'un abonnement sans fin
        :return: Nothing
        """
        if self._name not in ['horanet.subscription', 'horanet.package']:
            raise NotImplementedError('This method is meant to be used only on a subscription or package recordset')
        if compute_date and not isinstance(compute_date, str):
            raise ValueError("Argument compute_date must be an ORM date, not %s" % str(type(compute_date)))
        compute_date = compute_date or fields.Date.today()

        cycle_obj = self.env['horanet.subscription.cycle']

        for rec in self:
            sorted_lines = rec.line_ids.sorted('start_date')  # oldest first

            #########################################################################################
            # 0 - Update the renewable option to the closing date
            if not rec.is_renewable and not rec.closing_date and rec.cycle_id.period_type != 'unlimited':
                # En cas de nouveau contrat, ne garder qu'une période
                if not sorted_lines:
                    last_cycle_end_date = rec.cycle_id.get_end_date_of_cycle(rec.start_date)
                # Si le contrat à déjà des lignes, s'arréter à la dernière
                else:
                    last_cycle_end_date = rec.cycle_id.get_end_date_of_cycle(sorted_lines[-1].start_date)

                rec.closing_date = date_utils.convert_date_to_closing_datetime(last_cycle_end_date)

            #########################################################################################
            # 1 - Determine the compute period (include all that must be updated)
            # All subscription have an opening date and a start_date, get the oldest for computation
            compute_start_date = fields.Date.to_string(fields.Date.from_string(rec.opening_date))
            if compute_start_date > rec.start_date:
                compute_start_date = rec.start_date
            if sorted_lines and compute_start_date > sorted_lines[0].start_date:
                compute_start_date = sorted_lines[0].start_date

            compute_end_date = compute_date
            if rec.closing_date:
                compute_end_date = fields.Date.to_string(date_utils.convert_closing_datetime_to_date(rec.closing_date))
            if rec.end_date and compute_end_date < rec.end_date:
                compute_end_date = rec.end_date
            if sorted_lines and sorted_lines[-1].end_date and compute_end_date < sorted_lines[-1].end_date:
                compute_end_date = sorted_lines[-1].end_date
            # At this point compute_start_date <-> compute_end_date represent the existing subscription/lines
            # extended to the compute date if after existing date and contract renewable

            if compute_end_date < compute_start_date:
                # Can only append if the subscription has no lines with a start date in the future
                # Add a raise to be sure to catch an otherwise silent error (should not append)
                if rec.line_ids:
                    raise Exception('Unexpected error, please review the code')
                continue

            #########################################################################################
            # 2 - Iterate on the current cycle periods
            periods = rec.cycle_id.get_periods_of_cycle(compute_start_date, compute_end_date)

            for period in periods:
                # Get the existing lines on the period of interest
                existing_lines = rec.line_ids.filtered(
                    lambda l: l.start_date >= period[0] and (
                            not l.end_date or not period[1] or l.end_date <= period[1]))

                # postula : pas de hiatus entre les périodes existantes
                if existing_lines:
                    #########################################################################################
                    # 3 - Création/modification des lignes existante,
                    # il n'y à que trois cas de figure, car si il existe une(des) ligne(s) sur la période d'intérêt
                    # et qu'il n'y à pas de hiatus:
                    #  - dans le cas d'un cycle illimité, étendre les lignes
                    #  - dans le cas ou il manque un ligne au début, en créer une ou étendre l'existante
                    #  - dans le cas ou il manque un ligne à la fin, idem
                    # NB : les lignes existante ne sont pas étendues si non incluse dans le nouveau cycle (période)

                    sorted_existing_lines = existing_lines.sorted('start_date')
                    # Si le cycle est illimité, étendre la première et la dernière ligne (dans ce cas la date de debut
                    # de la première ligne est forcément supérieur ou égale à la date de début de période)
                    if not period[1]:
                        sorted_existing_lines[0].start_date = period[0]
                        if rec.closing_date:
                            sorted_existing_lines[-1].end_date = \
                                date_utils.convert_closing_datetime_to_date(rec.closing_date)
                        else:
                            sorted_existing_lines[-1].end_date = period[1]
                        continue
                    # Si il existe un manque de ligne au début de la période
                    if period[0] < sorted_existing_lines[0].start_date:
                        # Si la première ligne est incluse dans la nouvelle période, l'étendre
                        if sorted_existing_lines[0].end_date <= period[1]:
                            sorted_existing_lines[0].start_date = period[0]
                        # Sinon créer une nouvelle ligne (jusqu'a la période suivante)
                        else:
                            new_line = rec.line_ids._create_object_line(period[0], rec)
                            new_line.end_date = cycle_obj.get_previous_day_date(sorted_existing_lines[0].start_date)
                    # Si il existe un manque de ligne à la fin de la période
                    if period[1] > sorted_existing_lines[-1].end_date:
                        # Si la dernière ligne est incluse dans la nouvelle période, l'étendre
                        if sorted_existing_lines[-1].start_date >= period[0]:
                            sorted_existing_lines[-1].end_date = period[1]
                        # Sinon créer une nouvelle ligne (à partir de la période précédente)
                        else:
                            rec.line_ids._create_object_line(
                                cycle_obj.get_next_day_date(sorted_existing_lines[0], rec))
                # Si il n'existe aucune ligne sur la période, en créer une, pas de risque de chevauchement
                # (car la période d'interêt (donc existing_lines) inclus au minimum toute les lignes existantes,
                # notamment dans le cas d'un cycle illimité)
                if not existing_lines:
                    rec.line_ids._create_object_line(period[0], rec)

            #########################################################################################
            # 4 - Update the closing/opening date on the lines (from the subscription)
            rec_opening_time = fields.Datetime.from_string(rec.opening_date)
            rec_closing_time = fields.Datetime.from_string(rec.closing_date) if rec.closing_date else None
            for line in rec.line_ids:
                line_start_time = fields.Datetime.from_string(line.start_date)
                line_end_time = line.end_date and date_utils.convert_date_to_closing_datetime(line.end_date) or None
                # Si la date de d'ouverture appartient à cette ligne, la positionner, sinon prendre la date naturelle
                if line_start_time < rec_opening_time and (not line_end_time or rec_opening_time < line_end_time):
                    line.opening_date = rec_opening_time
                else:
                    line.opening_date = line_start_time
                # Si la date de fermeture appartient à cette ligne, la positionner, sinon prendre la date naturelle
                if rec_closing_time:
                    if line_start_time < rec_closing_time and (not line_end_time or rec_closing_time < line_end_time):
                        line.closing_date = rec_closing_time
                    else:
                        line.closing_date = line_end_time
                # Dans le cas ou le contrat n'a pas de date de fin, prendre la date naturelle des périodes
                # Cela fonctionne aussi pour l'illimité car seul la dernière ligne n'a pas de date de fin
                else:
                    line.closing_date = line_end_time

            #########################################################################################
            # 5 - Update the end and start date of the subscription (from the lines)
            sorted_lines = rec.line_ids.sorted('start_date')
            rec.start_date = sorted_lines[0].start_date
            rec.end_date = sorted_lines[-1].end_date

    @api.multi
    def _create_object_line(self, opening_date, parent):
        """TODO."""
        if self._name not in ['horanet.subscription.line', 'horanet.package.line']:
            raise NotImplementedError('This method is meant to be used only on a subscription or package recordset')
        result = None
        if self._name == 'horanet.subscription.line':
            result = self.create_subscription_line(opening_date, parent)
        if self._name == 'horanet.package.line':
            result = self.create_package_line(opening_date, parent)

        return result

    # endregion

    pass
