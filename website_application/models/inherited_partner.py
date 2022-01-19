import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """We add applications."""

    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    website_application_ids = fields.One2many(string="Requests", comodel_name='website.application',
                                              inverse_name='applicant_partner_id')
    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
