from odoo import models, fields


class AddNationalAndMobilePrefix(models.Model):
    # region Private attributes
    _inherit = 'res.country'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    national_prefix = fields.Text(string="National phone prefix", readonly=True)
    mobile_prefix = fields.Text(string="Mobile prefix", readonly=True)
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
