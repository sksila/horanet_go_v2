from odoo import api, models, _, SUPERUSER_ID
from odoo import exceptions


class User(models.Model):
    """Class to add a function in res.users."""

    _inherit = 'res.users'

    @api.multi
    @api.constrains('groups_id')
    def _check_groups(self):
        """Check that user is allowed to grant some access rights."""
        user = self.env.user
        if user.id == SUPERUSER_ID:
            return

        technical_settings_group = self.env.ref('base.group_no_one')
        configuration_group = self.env.ref('base.group_system')
        for rec in self:
            # Check if user wants to grant configuration setting
            if rec.id != user.id and configuration_group in rec.groups_id:
                raise exceptions.ValidationError(
                    _('Only your system administrator can grant this access right.')
                )
            # Check if user wants to grant technical setting
            if technical_settings_group in rec.groups_id and not user.has_group('base.group_system'):
                raise exceptions.ValidationError(
                    _('Only user in group {group_name} can grant this access right.'.format(
                        group_name=configuration_group.name))
                )
