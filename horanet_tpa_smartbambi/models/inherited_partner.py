# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from ..config.config import TPA_NAME

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Override partner model to add SmartBambi TPA synchronization membership."""

    # region Private attributes
    _inherit = 'res.partner'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    tpa_membership_smartbambi = fields.Boolean(string="Synchronize with SmartBambi", copy=False)
    tpa_membership_other_smartbambi = fields.Boolean(string="Synchronize with Other TPA SmartBambi", copy=False)

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    @api.onchange('tpa_membership_other_smartbambi')
    def _onchange_other_smartbambi(self):
        """Change membership of smartbambi if other smartbambi membership is edited.

        :return nothing
        """
        for rec in self:
            if rec.tpa_membership_other_smartbambi:
                rec.tpa_membership_smartbambi = True

    @api.onchange('tpa_membership_smartbambi')
    def _onchange_smartbambi(self):
        """Change membership of other smartbambi if smartbambi membership is edited.

        :return nothing
        """
        for rec in self:
            if not rec.tpa_membership_smartbambi:
                rec.tpa_membership_other_smartbambi = False

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
                if rec.tpa_membership_smartbambi:
                    tpa_synchronization_status_rec = rec.get_or_create_tpa_synchro_partner(TPA_NAME)
                    if self.env['collectivity.config.settings'].get_tpa_smartbambi_is_enable():
                        tpa_synchronization_status_rec.write({'ref_write_date': fields.Datetime.now()})
                        tpa_synchronization_status_rec.execute_method_in_thread('action_synchronization_smartbambi')

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
        if company_type_not_foyer and self.env.user.has_group('horanet_tpa_smartbambi.group_tpa_smartbambi'):
            vals.update({'tpa_membership_smartbambi': True})
        if company_type_not_foyer and self.env.user.has_group('horanet_tpa_smartbambi.group_tpa_other_smartbambi'):
            vals.update({'tpa_membership_other_smartbambi': True})
            vals.update({'tpa_membership_smartbambi': True})

        new_partner = super(ResPartner, self).create(vals)
        if new_partner.tpa_membership_smartbambi:
            tpa_synchronization_status_rec = new_partner.get_or_create_tpa_synchro_partner(TPA_NAME)
            if self.env['collectivity.config.settings'].get_tpa_smartbambi_is_enable():
                tpa_synchronization_status_rec.write({'ref_write_date': fields.Datetime.now()})
                tpa_synchronization_status_rec.execute_method_in_thread('action_synchronization_smartbambi')

        return new_partner

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
    pass
