# coding: utf-8

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)
MODULE_UNINSTALL_FLAG = '_force_unlink'


def migrate(cr, version):
    u"""Suppression du modèle horanet.file."""
    if not version:
        return

    with api.Environment.manage():
        model_name = 'horanet.file'
        # table_name = model_name.replace('.', '_')
        env = api.Environment(cr, SUPERUSER_ID, {MODULE_UNINSTALL_FLAG: True})

        context_flags = {MODULE_UNINSTALL_FLAG: True}

        env.cr.execute("SELECT model from ir_model WHERE model = 'horanet.file'")

        for model, in env.cr.fetchall():
            _logger.info('Purging model %s', model_name)
            attachments = env['ir.attachment'].search([('res_model', '=', model_name)])
            if attachments:
                env.cr.execute(
                    "UPDATE ir_attachment SET res_model = NULL WHERE id in %s",
                    (tuple(attachments.ids),))

            env['ir.model.constraint'].search([('model', '=', model_name), ]).unlink()
            relations = env['ir.model.fields'].search([('relation', '=', model_name)]).with_context(**context_flags)
            for relation in relations:
                try:
                    # Fails if the model on the target side
                    # cannot be instantiated
                    relation.unlink()
                except KeyError:
                    pass
                except AttributeError:
                    pass
            env['ir.model.relation'].search([('model', '=', model_name)]).with_context(**context_flags).unlink()

            env.cr.execute("DROP TABLE IF EXISTS horanet_file_horanet_subscription_rel")

            # check if the model still exist in the registry before deletion, to avoid key error in api
            if env.get(model_name, False):
                env['ir.model'].search([('model', '=', model_name)]).unlink()
            else:
                table_name = model_name.replace('.', '_')
                env.cr.execute("DROP TABLE IF EXISTS {table_name}".format(table_name=table_name))

            env.cr.execute("DELETE from ir_model where model = '{model_name}'".format(model_name=model_name))

    _logger.info('End suppression model horanet.file')
