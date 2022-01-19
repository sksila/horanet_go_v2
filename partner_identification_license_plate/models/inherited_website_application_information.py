# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WebsiteApplicationInformation(models.Model):
    # region Default methods
    # endregion

    # region Private attributes
    _inherit = 'application.information'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    type = fields.Selection(
        string="Type",
        selection_add=[('license_plate', "License Plate")],
        required=True,
        help="""'number': number input field\n
            'text': one-line text input field\n
            'option': radio button to get a boolean value\n
            'selection': selection box with custom choice values\n
            'date': date input field\n
            'model': selection box with values from corresponding model\n
            'document': document input field\n
            'explanation': informative html field\n
            'license_plate': a text field for license plate"""
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
    def get_type_to_field(self, field_type):
        value = super(WebsiteApplicationInformation, self).get_type_to_field(field_type)

        if field_type == 'license_plate':
            return 'value_text'
        return value

    @api.multi
    def get_by_record(self):
        self.ensure_one()
        value = super(WebsiteApplicationInformation, self).get_by_record()
        if self.type in ('text', 'selection', 'license_plate'):
            return self.value_text
        else:
            return value

    # endregion

    pass
