
from odoo import _, fields, models


class EcopadTransaction(models.Model):
    _name = 'environment.ecopad.transaction'
    _sql_constraints = [
        ('unicity_on_number_and_session', 'UNIQUE(number, ecopad_session_id)',
         _('The transaction number must be unique per ecopad session'))
    ]

    number = fields.Char(required=True)
    ecopad_session_id = fields.Many2one(
        string="Ecopad Session",
        comodel_name='environment.ecopad.session',
        required=True
    )
    operation_ids = fields.One2many(
        string="Operations",
        comodel_name='horanet.operation',
        inverse_name='ecopad_transaction_id'
    )
    ecopad_signature = fields.Binary(string="Signature")
