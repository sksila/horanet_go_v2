from odoo import models, fields, _, api, exceptions
from ..config import config


class HoranetAction(models.Model):
    # region Private attributes
    _name = 'horanet.action'
    _sql_constraints = [('unicity_on_code', 'UNIQUE(code)', _("The action code must be unique"))]

    # endregion

    # region Default methods
    def default_code(self):
        """Get the default code from a sequence."""
        return self.env['ir.sequence'].next_by_code('action.code')

    # endregion

    # region Fields declaration
    code = fields.Char(
        string="Reference",
        required=True,
        default=default_code)
    name = fields.Char(
        string="Name",
        translate=True,
        required=True)
    type = fields.Selection(
        string="Type",
        selection=config.ACTION_MODE,
        help="An action typed query is an action that require a response",
        default='operation',
        required=True)
    description = fields.Text(
        string="Description")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('code')
    def check_code(self):
        """Force the action code to start with an underscore.

        Only action in data installed with the module can start with an underscore (default actions)
        :raise: Validation error if a user try to create an action with a code not starting with an underscore
        """
        if self.env.context.get('install_mode', False):
            return
        for action in self:
            if not action.code.startswith('_'):
                raise exceptions.ValidationError(_("The (custom) action code must start with an underscore"))

    # endregion

    # region CRUD (overrides)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
