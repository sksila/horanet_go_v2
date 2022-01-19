import uuid

from odoo import models, fields, _, api


class Device(models.Model):
    # region Private attributes
    _name = 'horanet.device'
    _sql_constraints = [('unicity_on_unique_id', 'UNIQUE(unique_id)', _("The unique_id must be unique !"))]

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(
        string="Name",
        required=True)
    unique_id = fields.Char(
        string="Unique ID",
        required=True,
        index=True,
        copy=False,
        default=lambda self: uuid.uuid1())

    description = fields.Text(
        string="Description")
    check_point_ids = fields.One2many(
        string="Check point",
        comodel_name='device.check.point',
        inverse_name='device_id',
    )

    device_detail = fields.Text(
        string="Details",
        default='---',
        help="Informations send by the device, the content depends on the device type and software version",
    )
    last_communication_time = fields.Datetime(
        string="Last communication",
        readonly=True,
        store=True,
        help="Time at which the device communicated with the server for the last time (with the web API)",
    )
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
    def update_last_communication_time(self, communication_time=None):
        """Reset the last communication time of the device.

        This method is used by the web api to provide informations regarding the last date of the api call.
        """
        communication_time = communication_time or fields.Datetime.now()
        self.last_communication_time = communication_time

    # endregion

    pass
