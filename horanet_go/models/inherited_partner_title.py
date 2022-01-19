from odoo import models, fields


class PartnerTitle(models.Model):
    """Class that inherit res.partner.title to add active field and company specific title."""

    # region Private attributes
    _inherit = 'res.partner.title'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration

    active = fields.Boolean(default=True)
    is_company_title = fields.Boolean(string='is Company Title', default=False)

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
