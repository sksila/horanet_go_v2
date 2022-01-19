import logging
from odoo import SUPERUSER_ID, api

_logger = logging.getLogger('odoo.addons.horanet_go')


def pre_init_hook(cr):
    """Pre-install script permettant le re-nomage de horanet_collectivity en horanet_GO."""
    _logger.info('Rename of old ir_model_data')
    cr.execute("UPDATE ir_model_data SET name = 'group_horanet_go_admin' "
               "WHERE name = 'group_horanet_collectivity_admin' AND module = 'horanet_collectivity'")
    cr.execute("UPDATE ir_model_data SET name = 'group_horanet_go_agent' "
               "WHERE name = 'group_horanet_collectivity_agent' AND module = 'horanet_collectivity'")
    cr.execute("UPDATE ir_model_data SET name = 'group_horanet_go_citizen' "
               "WHERE name = 'group_horanet_collectivity_citizen' AND module = 'horanet_collectivity'")
    cr.execute("UPDATE ir_model_data SET module = 'horanet_go' WHERE module = 'horanet_collectivity'")
    _logger.info('Update dependencies to horanet_go')
    cr.execute("UPDATE ir_module_module_dependency SET name = 'horanet_go' WHERE name = 'horanet_collectivity'")


def post_init_hook(cr, registry):
    """Post-install script. Suppression de la référence d'horanet_collectivity de la liste des modules."""
    _logger.info("Suppression of horanet_collectivity from registry")
    env = api.Environment(cr, SUPERUSER_ID, {})

    collectivity_module = env['ir.module.module'].search([('name', '=', 'horanet_collectivity')])
    if collectivity_module:
        env['ir.model.constraint'].search([('module', '=', collectivity_module.id)]).unlink()
        collectivity_module.write({'state': 'uninstalled'})
        collectivity_module.unlink()
