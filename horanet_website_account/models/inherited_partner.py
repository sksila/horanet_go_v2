from odoo import fields, models


class InheritedPartner(models.Model):
    # region Private attributes
    _inherit = 'res.partner'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    vat_number = fields.Char(string="VAT number")
    siret_code = fields.Char(string="SIRET/SIREN")
    ape_code = fields.Char(string="APE code")
    # endregion

    # region Fields method
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
