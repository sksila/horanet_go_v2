import logging

from odoo import models, fields, api
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    """Surcharge du modèle partner pour modifier la gestion du login."""

    # region Private attributes
    _inherit = 'res.users'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    state = fields.Selection(search='_search_state')

    # endregion

    # region Fields method
    @api.model
    def _search_state(self, operator, value):
        """Search users by state field value.

        :param operator: One of this following fields : '=', '!=', '=like', '=ilike', 'like', 'not like', 'ilike',
            'not ilike'
        :param value: 'new' or 'active'
        :return: res.users search domain
        """
        result = expression.FALSE_DOMAIN
        if operator in ['=', '!=', '=like', '=ilike', 'like', 'not like', 'ilike', 'not ilike']:
            if isinstance(value, str):
                active_ids = self.env['res.users.log'].search([('create_uid', '!=', False)]).mapped('create_uid')
                result = [('id', 'in', active_ids.ids)]
                if bool(value == 'active') == bool(operator in expression.NEGATIVE_TERM_OPERATORS):
                    result = [expression.NOT_OPERATOR] + result
        return expression.normalize_domain(result)

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def write(self, vals):
        """Override write method to send mail when the user connect for the 1st time, set him connected and active."""
        for rec in self:
            if vals.get('password') and not rec.password and self.state == 'new':
                # On met le partner en connected dans son workflow et en active True
                partner = rec.env['res.users'].search([('id', '=', rec.id)])
                partner.partner_id.write({'status': 'connected', 'active': True})
        return super(ResUser, self).write(vals)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def _cron_delete_invalid_signup(self):
        u"""Cron de suppression des users et partners associés ayant des demandes d'inscription non abouties.

        Ce cron supprime les utilisateurs qui ce sont enregistrés via le front mais qui n'ont jamais été saisir leurs
        mot de passe (inscription non abouties) ainsi que les users crées après le partner via le bouton 'créer un
        accès au poratil' mais où le mot de passe n'a jamais été renseigné. Dans ce dernier cas on ne supprime que
        le user.
        La recherche de ces utilisateurs ce fait via les critères suivant:
            - Date de creation inferieur au temps limit d'inscription (options)
            - L'état du user est à 'jamais connecté' (new)
            - Le user n'est pas un utilisateur interne (share = True)
            - Le partner associé est archivé (cas d'une incription via le front)
            - La date de création du partner et du user sont les mêmes (on s'assure que le partner a été crée via
            une création d'un user.

        La date limite est calculée à partir du moment présent moins une durée en heure (durée saisie dans la
        configuration générale 'base.config.settings', par default 360h soit 15 jours).
        """
        _logger.info("Start CRON delete inactive signup")

        limit_hours = self.env['base.config.settings'].get_invalid_signup_limit_hours()
        min_time_search = datetime.now() - relativedelta(hours=int(limit_hours))

        # recherche des users à l'état 'jamais connecté'
        invalid_users = self.env['res.users'].search(
            [('create_date', '<', fields.Datetime.to_string(min_time_search)),
             ('state', '=', 'new'),
             ('share', '=', True),
             ])

        if invalid_users:
            for invalid_user in invalid_users:
                invalid_partner = self.env['res.partner'].browse(invalid_user.partner_id.id)

                if invalid_partner.create_date == invalid_user.create_date and invalid_partner.active is False:
                    # user crée via le front (inscription non aboutie)
                    invalid_user.unlink()
                    invalid_partner.unlink()

                elif invalid_partner.create_date != invalid_user.create_date and invalid_partner.active is True:
                    # user crée (mais jamais utilisé) après le partner via le bouton 'créer un accès au portail'
                    invalid_user.unlink()

        _logger.info("End CRON delete inactive signup")
    # endregion

    pass
