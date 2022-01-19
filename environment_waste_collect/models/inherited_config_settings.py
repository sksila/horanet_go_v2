import logging

from odoo import fields, models, api
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class WasteConfigSettings(models.TransientModel):
    # region Private attributes
    _inherit = 'horanet.environment.config'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    group_manage_container = fields.Selection([
        (0, "Do not manage containers"),
        (1, "Manage containers")], "Containers",
        implied_group='environment_waste_collect.group_manage_containers',
        help="Allows users to manage containers if they own them")

    is_linked_to_smarteco = fields.Boolean(string="Link to SmartEco")

    module_environment_equipment = fields.Boolean(
        string="Manage personal and collective containers",
        help="Manage personal and collective containers")

    # Ces paramètres sont envoyés à l'Ecopad
    print_ticket_transaction = fields.Boolean(string="Print a ticket a the end of the transaction")
    client_signature_required = fields.Boolean(string="A client signature is required")
    ecopad_tag_ext_reference_label = fields.Char(string="Label of external reference field on Ecopad")

    ecopad_can_assign_medium = fields.Boolean(string="Authorize Ecopads to assign medium")

    ecopad_cache_data_activated = fields.Selection(
        string="Activate Ecopad API cached data AND generate cache",
        selection=[('yes', "Yes"), ('no', "No")],
        help="Activate or deactivate the CRON that generate periodically the cached data"
    )
    ecopad_cache_data_activated_state = fields.Boolean(string="Technical")

    ecopad_access_mode_configuration = fields.Selection(
        string="Ecopad access mode configuration",
        selection=[('always_on', "Always ON"), ('always_off', "Always OFF"), ('configurable', "Configurable")],
        help="If 'always ON or OFF', the option will be locked on the Ecopad, if 'configurable'"
             " the Ecopad user could change the value.",
        default='configurable'
    )

    enable_setup_and_close_wizards = fields.Boolean(
        string="Enable Setup and Close wizards",
        help="Enable or disable Setup and Close wizards buttons for environment partners",
    )
    # endregion

    # region Fields method

    # Trick: get_default_ methods are called every time, use only one for all fields
    @api.model
    def get_default_waste_collect_config(self, _):
        """Get default config of Environment settings.

        :return configuration object
        """
        # We use safe_eval on the result, since the value of the parameter is a nonempty string
        ICP = self.env['ir.config_parameter'].sudo()
        return {
            'is_linked_to_smarteco': safe_eval(
                ICP.get_param('environment_waste_collect.is_linked_to_smarteco', 'False')),
            'print_ticket_transaction': safe_eval(
                ICP.get_param('environment_waste_collect.print_ticket_transaction', 'False')),
            'client_signature_required': safe_eval(
                ICP.get_param('environment_waste_collect.client_signature_required', 'False')),
            'ecopad_tag_ext_reference_label': self.get_tag_external_reference_label_ecopad(),
            'ecopad_can_assign_medium': self.get_ecopad_can_assign_medium(),
            'ecopad_cache_data_activated': 'yes' if self.get_ecopad_cache_data_cron().active else 'no',
            'ecopad_cache_data_activated_state': self.get_ecopad_cache_data_cron().active,
            'ecopad_access_mode_configuration': self.get_ecopad_access_mode_configuration(),
            'enable_setup_and_close_wizards': self.get_enable_setup_and_close_wizards(),
        }

    @api.multi
    def set_waste_collect_config(self):
        ICP = self.env['ir.config_parameter'].sudo()
        # we store the repr of the values, since the value of the parameter is a required string
        ICP.set_param('environment_waste_collect.is_linked_to_smarteco', str(self.is_linked_to_smarteco))
        ICP.set_param('environment_waste_collect.print_ticket_transaction', str(self.print_ticket_transaction))
        ICP.set_param('environment_waste_collect.client_signature_required', str(self.client_signature_required))
        ICP.set_param('environment_waste_collect.enable_setup_and_close_wizards', str(self.enable_setup_and_close_wizards))
        if self.ecopad_access_mode_configuration != self.get_ecopad_access_mode_configuration():
            ICP.set_param('environment_waste_collect.ecopad_access_mode_configuration',
                          str(self.ecopad_access_mode_configuration))
        if self.ecopad_tag_ext_reference_label != self.get_tag_external_reference_label_ecopad():
            ICP.set_param('environment.ecopad_tag_ext_reference_label',
                          str(self.ecopad_tag_ext_reference_label))
        if self.ecopad_can_assign_medium != self.get_ecopad_can_assign_medium():
            ICP.set_param('environment_waste_collect.ecopad_can_assign_medium', str(self.ecopad_can_assign_medium))
        # gestion du CRON et du cache de l'API Ecopdad
        ecopad_cache_cron = self.get_ecopad_cache_data_cron()
        if bool(self.ecopad_cache_data_activated == 'yes') != ecopad_cache_cron.active:
            if self.ecopad_cache_data_activated == 'yes':
                # Préparer le premier jeu de donnée en cache
                ecopad_cache_cron.method_direct_trigger()

            ecopad_cache_cron.active = self.ecopad_cache_data_activated == 'yes'

    @api.multi
    def get_ecopad_cache_data_cron(self):
        """Get the ecopad cache CRON."""
        return self.env.ref('environment_waste_collect.cron_ecopad_synchronization_cached_file')

    @api.multi
    def get_tag_external_reference_label_ecopad(self):
        """Get the tag external reference config key value.

        :return: the value of the key
        """
        ICP = self.env['ir.config_parameter'].sudo()
        return ICP.get_param("environment.ecopad_tag_ext_reference_label", "Other informations")

    @api.multi
    def get_ecopad_can_assign_medium(self):
        """Get the ecopad possibility to assign medium config key value.

        :return: the value of the key
        """
        ICP = self.env['ir.config_parameter'].sudo()
        return safe_eval(ICP.get_param("environment_waste_collect.ecopad_can_assign_medium", "False"))

    @api.multi
    def get_ecopad_access_mode_configuration(self):
        """Get the default access mode option for Ecopad.

        :return: the value of the key
        """
        ICP = self.env['ir.config_parameter'].sudo()
        return ICP.get_param("environment_waste_collect.ecopad_access_mode_configuration", "configurable")

    @api.multi
    def get_enable_setup_and_close_wizards(self):
        """Get the default option for setup and close wizards.

        :return: the value of the key
        """
        icp = self.env['ir.config_parameter']
        return safe_eval(icp.get_param('environment_waste_collect.enable_setup_and_close_wizards', 'True'))

    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_generate_cached_data(self):
        self.ensure_one()
        _logger.info("Start manual cache computation")

        self.get_ecopad_cache_data_cron().method_direct_trigger()

        _logger.info("End manual cache computation")

    # endregion

    # region Model methods

    # endregion
