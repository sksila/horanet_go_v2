from odoo import models, fields


class ResCountryState(models.Model):
    """Surcharge du modèle country.state pour y ajouter les res.city."""

    # region Private attributes
    _inherit = 'res.country.state'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    city_ids = fields.One2many(comodel_name='res.city', inverse_name='country_state_id', string='Cities')
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
