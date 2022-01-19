# -*- coding: utf-8 -*-

import logging
import threading

import odoo
from odoo import SUPERUSER_ID
from odoo import models, fields, api

INFO, WARNING, ERROR = 'info', 'warning', 'error'

_logger = logging.getLogger('pes_message')


class CenterMessage(models.Model):
    # region Private attributes
    _name = 'pes.message'
    _description = 'Messages'
    _order = 'date desc'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Code", size=64, required=True)
    message = fields.Text(string="Message", required=True)
    date = fields.Datetime(string="Date", default=lambda self: fields.Datetime.now(), readonly=True, required=True)
    type = fields.Selection(
        string="State",
        selection=[(INFO, "Information"), (ERROR, "Error"), (WARNING, "Warning")],
        default='info',
        readonly=True,
        required=True,
    )
    state = fields.Selection(
        string="State",
        selection=[('unread', "Unread"), ('read', "Read")],
        default='unread',
        readonly=True,
        required=True,
    )
    application_id = fields.Many2one(string="Application", comodel_name='pes.application', required=True)
    pes_declaration_id = fields.Many2one(string="Declaration", comodel_name='pes.declaration')
    declaration_file_id = fields.Many2one(string="Declaration file", comodel_name='pes.declaration.file')

    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def action_mark_as_read(self):
        for obj in self:
            obj.state = 'read'

    @api.multi
    def action_mark_as_unread(self):
        for obj in self:
            obj.state = 'unread'

    # endregion

    # region Model methods
    @api.model
    def get_application(self, application):
        if not application:
            application = self.env['pes.application'].search([], limit=1)
        if isinstance(application, basestring):
            application = self.env['pes.application'].search([
                '|',
                ('name', '=', application),
                ('code', '=', application),
            ], limit=1)
        elif isinstance(application, (int, long)):
            application = self.env['pes.application'].browse(application)
        if not application:
            application = self.env['pes.application'].search([], limit=1)
        return application

    # Les nom du champ de l'objet concerné par le message d'erreur doit être le même pour tous les objets
    @api.model
    def post_message(self, message, message_type, application=False, name=False, obj=False):
        message_type = message_type.lower().strip() if message_type else message_type
        self = self.sudo()
        threaded_post_message = threading.Thread(
            target=self._post_message,
            args=(self.env.cr.dbname, message, message_type, application, name, obj))
        threaded_post_message.start()

    @api.model
    def _post_message(self, db, message, message_type, application, name, obj):
        try:
            with api.Environment.manage():
                cr = odoo.registry(db).cursor()
                env = api.Environment(cr, SUPERUSER_ID, {})
                application = env['pes.message'].get_application(application)
                env['pes.message'].try_post_message(message, message_type, application, name)
                cr.commit()
                cr.close()
        except Exception as e:
            _logger.error(e.message)

    @api.model
    def try_post_message(self, message, message_type, application, name):
        assert message, 'You should specify a message to post'
        assert message_type in [INFO, WARNING, ERROR], 'The message type %s is not implemented' % message_type
        existing_messages = self.search([
            ('name', '=', name),
            ('type', '=', message_type),
            ('message', '=', message),
            ('application_id', '=', application.id),
        ])
        if existing_messages:
            for existing_message in existing_messages:
                existing_message.state = 'unread'
                existing_message.date = fields.Datetime.now()
        else:
            return self.create({
                'name': name,
                'type': message_type,
                'message': message,
                'application_id': application.id
            })
    # endregion
