# -*- coding: utf-8 -*-
# 1 : imports of python lib
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class TerminalLB7Configure(models.TransientModel):
    """Allow export of configuration properties in configured directory for selected terminals."""

    # region Private attributes
    _name = 'tco.terminal.lb7.configure'

    # endregion

    # region Default methods
    @api.model
    def _get_number_element(self):
        return self.env['tco.terminal'].search_count([
            ('id', 'in', self.env.context.get('active_ids')),
            ('model', '=', 'lb7'),
            ('is_active', '=', True),
        ])

    # endregion

    # region Fields declaration
    nb_element = fields.Integer(string='Number', default=_get_number_element)
    message = fields.Text(string='Information message', default="Click on Configure button")

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def configure_action(self):
        """Generate configuration csv files for LB7 terminals.

        Method used by configure_action button in wizard Form.
        :return: context information.
        """
        msg_display_list = []
        linefeed = "\n"
        first_terminal = self.with_context(active_test=False).browse(self.ids[0])

        _logger.info("Start LB7 Terminals configuration")

        terminal_recs = self.env['tco.terminal'].search([
            ('id', 'in', self.env.context.get('active_ids')),
            ('model', '=', 'lb7'),
            ('is_active', '=', True),
        ])

        header_message = "{} terminal(s) to configure".format(len(terminal_recs)) + linefeed

        # Generate setting files for selected terminals
        errors_msg = terminal_recs.lb7_generate_all_files() or []
        for error_msg in errors_msg:
            msg_display_list.insert(len(msg_display_list), error_msg)

        if len(msg_display_list) > 0 and len(msg_display_list[0]) > 0:
            global_message = header_message + "Terminals LB7 configuration terminated with {} error(s) :".format(
                len(msg_display_list)) + linefeed

            for msg_rec in msg_display_list:
                global_message += ''.join(msg_rec + linefeed)

            first_terminal.message = global_message
        else:
            first_terminal.message = header_message + "Terminals configuration terminated without error."

        _logger.info("End Terminals LB7 configuration")

        return {
            'type': 'ir.actions.act_window',
            'res_model': first_terminal._name,
            'res_id': first_terminal.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # endregion

    # region Model methods

    # endregion

    pass
