from odoo import models, fields, api


class DeviceCheckPoint(models.Model):
    # region Private attributes
    _name = 'device.check.point'

    # endregion

    # region Default methods
    def default_code(self):
        return self.env['ir.sequence'].next_by_code('device.check.point.code')

    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Reference", required=True, default=default_code)

    device_id = fields.Many2one(string="Device", comodel_name='horanet.device')
    input_activity_sector_id = fields.Many2one(string="Input activity sector", comodel_name='activity.sector',
                                               required=True)

    output_activity_sector_id = fields.Many2one(string="Ouput activity sector", comodel_name='activity.sector')

    activity_ids = fields.Many2many(string="Inherited activity", comodel_name='horanet.activity',
                                    related='input_activity_sector_id.activity_ids', readonly=True)
    activity_ids_dummy = fields.Many2many(string="Inherited activity",
                                          comodel_name='horanet.activity',
                                          compute='_compute_activity_ids_dummy',
                                          readonly=True)
    infrastructure_id = fields.Many2one(string="Infrastructure", comodel_name='horanet.infrastructure')

    # endregion

    # region Fields method
    @api.depends('input_activity_sector_id')
    def _compute_activity_ids_dummy(self):
        for rec in self:
            rec.activity_ids_dummy = rec.input_activity_sector_id and rec.input_activity_sector_id.activity_ids or False

    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = rec.name + ' (' + rec.code + ')'
            res.append((rec.id, name))
        return res

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
