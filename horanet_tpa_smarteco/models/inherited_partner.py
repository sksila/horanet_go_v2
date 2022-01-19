# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from ..config.config import TPA_NAME

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Override partner model to add SmartEco TPA synchronization membership."""

    # region Private attributes
    _inherit = 'res.partner'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    tpa_membership_smarteco = fields.Boolean(string="Synchronize with SmartEco", copy=False)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def write(self, vals):
        """Override write to update tpa_synchronization if needed, after calling the write method.

        :param vals: Edited values from formulary
        :return nothing
        """
        res = super(ResPartner, self).write(vals)
        fields_not_tpa = set(['active', 'company_id', 'signup_type', 'signup_expiration', 'signup_token', 'status'])
        if len(set(vals.keys()) - fields_not_tpa):
            for rec in self:
                if rec.tpa_membership_smarteco:
                    tpa_synchronization_status_rec = rec.get_or_create_tpa_synchro_partner(TPA_NAME)
                    if self.env['collectivity.config.settings'].get_tpa_smarteco_is_enable():
                        tpa_synchronization_status_rec.write({'ref_write_date': fields.Datetime.now()})
                        tpa_synchronization_status_rec.execute_method_in_thread('action_synchronization_smarteco')

        return res

    @api.model
    def create(self, vals):
        """Override to create a tpa_synchronization record if needed.

        :param vals: New values from formulary
        :return nothing
        """
        company_type_not_foyer = True
        if vals.get("company_type") and vals["company_type"] == 'foyer':
            company_type_not_foyer = False

        if company_type_not_foyer and self.env.user.has_group('horanet_tpa_smarteco.group_tpa_smarteco'):
            vals.update({'tpa_membership_smarteco': True})

        new_partner = super(ResPartner, self).create(vals)
        if new_partner.tpa_membership_smarteco:
            tpa_synchronization_status_rec = new_partner.get_or_create_tpa_synchro_partner(TPA_NAME)
            if self.env['collectivity.config.settings'].get_tpa_smarteco_is_enable():
                tpa_synchronization_status_rec.write({'ref_write_date': fields.Datetime.now()})
                tpa_synchronization_status_rec.execute_method_in_thread('action_synchronization_smarteco')

        return new_partner

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
    pass
