# coding: utf-8

from odoo import models, fields, api
from odoo.tools import safe_eval


class EnvironmentConfig(models.TransientModel):
    _inherit = 'horanet.environment.config'

    allow_multiple_moves_on_same_production_point = fields.Boolean()

    @api.model
    def get_default_allow_multiple_moves_on_same_production_point(self, _):
        icp_model = self.env['ir.config_parameter']

        return {
            'allow_multiple_moves_on_same_production_point': safe_eval(
                icp_model.get_param('environment_production_point.allow_multiple_moves_on_same_production_point',
                                    'False')
            )
        }

    def set_allow_multiple_moves_on_same_production_point(self):
        icp_model = self.env['ir.config_parameter']
        icp_model.set_param('environment_production_point.allow_multiple_moves_on_same_production_point',
                            repr(self.allow_multiple_moves_on_same_production_point))
