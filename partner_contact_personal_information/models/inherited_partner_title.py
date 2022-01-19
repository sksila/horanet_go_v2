from odoo import fields, models

from ..config import config


class ResPartnerTitle(models.Model):
    # region Private attributes
    _inherit = 'res.partner.title'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    gender = fields.Selection(string='Gender', selection=config.PARTNER_GENDER, default='neutral')
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
