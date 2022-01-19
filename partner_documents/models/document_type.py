from odoo import fields, models


class DocumentType(models.Model):
    # region Private attributes
    _name = 'ir.attachment.type'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(required=True, translate=True)
    validity_period = fields.Integer(string="Period of validity (in days)")
    technical_name = fields.Char(string="Technical name")
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
