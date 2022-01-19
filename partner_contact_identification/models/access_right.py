from odoo import fields, models


class AccessRight(models.Model):
    # region Private attributes
    _name = 'partner.contact.identification.access.right'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    partner_id = fields.Many2one(
        string="Partner",
        comodel_name='res.partner'
    )
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
