
from odoo import api, fields, models


class Container(models.Model):

    _name = 'environment.container'
    _inherit = 'maintenance.equipment'

    name = fields.Char(string="Reference", required=True, translate=False)
    assign_date = fields.Datetime(string="Assigned Date", track_visibility='onchange')
    waste_site_id = fields.Many2one(
        string="Waste site",
        comodel_name='environment.waste.site'
    )
    emplacement_id = fields.Many2one(
        string="Emplacement",
        comodel_name='stock.emplacement',
        domain="[('waste_site_id', '=', waste_site_id)]"
    )
    filling_level = fields.Integer(
        related='emplacement_id.filling_level',
        readonly=True
    )
    activity_id = fields.Many2one(
        related='emplacement_id.activity_id',
        readonly=True
    )
    container_type_id = fields.Many2one(
        string="Type",
        comodel_name='environment.container.type'
    )
    volume = fields.Integer(
        related='container_type_id.volume',
        readonly=True
    )
    picture = fields.Binary(string="Picture")

    # region Constrains and Onchange
    @api.onchange('emplacement_id')
    def onchange_emplacement(self):
        if self.emplacement_id:
            self.assign_date = fields.Datetime.now()
    # endregion
