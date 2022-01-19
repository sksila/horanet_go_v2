# -*- coding: utf-8 -*-

import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    """Override user model to manage membership of partner associated."""

    # region Private attributes
    _inherit = 'res.users'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def _signup_create_user(self, values):
        user = super(ResUser, self)._signup_create_user(values)
        if user.has_group('horanet_tpa_aquagliss.group_tpa_aquagliss'):
            user.tpa_membership_aquagliss = True
        return user

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
