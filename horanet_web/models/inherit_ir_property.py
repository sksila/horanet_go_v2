from odoo import models, api


class IrProperty(models.Model):
    """Add tool method to facilitate usages."""

    # region Private attributes
    _inherit = 'ir.property'

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
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def set_property_many2one(self, field_name, rec, model_name):
        """Add the value to a unique property.

        Create the property
        :param field_name: name of the field related to the model in self
        :param value: the binary value
        :return: Nothing
        """
        ir_property_obj = self.env['ir.property']

        ir_property_rec = ir_property_obj.search([('name', '=', field_name)])

        value_binary = ''
        if rec and rec.id:
            value_binary = str(rec._name + "," + rec.id)

        field_rec = self.env['ir.model.fields'].search([('name', '=', field_name), ('model', '=', model_name)])
        if not ir_property_rec:
            ir_property_obj.create({
                'name': field_name,
                'fields_id': field_rec.id,
                'type': 'many2one',
                'value_reference': value_binary,
            })
        else:
            ir_property_rec.value_binary = value_binary

    @api.model
    def set_property_binary(self, field_name, value, model_name):
        """Add the value to a unique property.

        Create the property
        :param field_name: name of the field related to the model in self
        :param value: the binary value
        :return: Nothing
        """
        ir_property_obj = self.env['ir.property']

        ir_property_rec = ir_property_obj.search([('name', '=', field_name)])

        field_rec = self.env['ir.model.fields'].search([('name', '=', field_name), ('model', '=', model_name)])
        if not ir_property_rec:
            ir_property_obj.create({
                'name': field_name,
                'fields_id': field_rec.id,
                'type': 'binary',
                'value_binary': value,
            })
        else:
            ir_property_rec.value_binary = value

    # endregion

    pass
