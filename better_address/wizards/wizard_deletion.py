from odoo import models, fields, api


class Wizard(models.TransientModel):
    """Class containing wizard methods."""

    # region Private attributes
    _name = 'horanet.wizard.deletion'

    # endregion

    # region Default methods
    @api.model
    def _get_default_number_element(self):
        """Get the number of records of a model specified by the key 'active_model' in the context.

        :return: number of records
        """
        num = 0
        if self.env.context.get('active_model'):
            num = self.env[self.env.context.get('active_model')].search_count([])
        return num
        # return {'value': {'nb_element': 45}}

    @api.model
    def _get_type_element_src(self):
        """Get the name of model  specified by the key 'active_model' in the context.

        :return: name the model
        """
        name = 'element'
        if self.env.context.get('active_model'):
            name = self.env.context.get('active_model')
        return name
        # return {'value': {'nb_element': 45}}

    # endregion

    # region Fields declaration
    nb_element = fields.Integer(string='Number', default=_get_default_number_element)
    type_element = fields.Char(string='Element', default=_get_type_element_src, )

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
    @api.multi
    def delete_all(self):
        """Delete all records for a given model in the context."""
        if self.env.context.get('active_model'):
            self.env[self.env.context.get('active_model')].search([]).unlink()

    # endregion

    pass
