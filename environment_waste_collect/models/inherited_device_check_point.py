
import uuid
from odoo import models, fields, api
from odoo.osv import expression


class DeviceCheckPointIP(models.Model):
    # region Private attributes
    _inherit = 'device.check.point'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    ip_address = fields.Char(string="Private IP")

    device_unique_id = fields.Char(related='device_id.unique_id')

    environment_waste_site_id = fields.Many2one(
        comodel_name='environment.waste.site',
        string='Waste site',
        compute='_compute_environment_waste_site_id',
        inverse='_inverse_environment_waste_site_id',
        search='_search_environment_waste_site_id',
        store=False)

    # endregion

    # region Fields method
    @api.depends('infrastructure_id')
    def _compute_environment_waste_site_id(self):
        """Get waste site from infrastruture."""
        waste_site_model = self.env['environment.waste.site'].sudo()
        for rec in self:
            if rec.infrastructure_id:
                waste_site_ids = waste_site_model.search([('infrastructure_id', '=', rec.infrastructure_id.id)])
                if waste_site_ids and len(waste_site_ids) == 1:
                    rec.environment_waste_site_id = waste_site_ids

    @api.multi
    def _inverse_environment_waste_site_id(self):
        """Set infrastructure from waste site."""
        for rec in self:
            if rec.environment_waste_site_id:
                waste_site_model = self.env['environment.waste.site'].sudo()
                waste_site = waste_site_model.browse(rec.environment_waste_site_id.id)
                if waste_site:
                    rec.infrastructure_id = waste_site.infrastructure_id

    @api.model
    def _search_environment_waste_site_id(self, operator, value=False):
        """Search check points by waste site name or id."""
        result = expression.FALSE_DOMAIN
        environment_waste_site_model = self.env['environment.waste.site']
        if operator in ['=like', '=ilike',
                        'like', 'not like', 'ilike', 'not ilike']:
            filtered_waste_sites = environment_waste_site_model.search([('name', operator, value)])
            result = [('infrastructure_id', 'in', filtered_waste_sites.mapped('infrastructure_id').ids)]
        elif operator in ['in', 'not in', '=', '!='] and isinstance(value, list):
            filtered_waste_sites = environment_waste_site_model.browse(value)
            result = [('infrastructure_id', 'in', filtered_waste_sites.mapped('infrastructure_id').ids)]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            result = expression.NOT_OPERATOR + result

        return result
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    @api.multi
    def write(self, vals):
        """
        Override write to rename linked device like the check point.

        The environment Terminal is a concept merging a check point to a device : if the context key
        'auto_manage_terminal' is set, the linked device'name will be changed to match the checkpoint.
        """
        if vals.get('name', False) and 'auto_manage_terminal' in self.env.context:
            for rec in self:
                if rec.device_id and len(rec.device_id.check_point_ids) < 2:
                    rec.device_id.write({'name': vals['name']})

        return super(DeviceCheckPointIP, self).write(vals)

    @api.model
    def create(self, vals):
        """
        Override create to create and link a device to the check point.

        The environment Terminal is a concept merging a check point to a device : if the context key
        'auto_manage_terminal' is set, a device record will be created and linked to the checkpoint.
        """
        horanet_device_model = self.env['horanet.device'].sudo()
        if 'auto_manage_terminal' in self.env.context:
            if not vals.get('device_unique_id', False):
                vals.update({'device_unique_id': uuid.uuid1()})

            new_device = horanet_device_model.create({
                'name': vals['name'],
                'unique_id': vals['device_unique_id']
            })

            vals.update({'device_id': new_device.id})

        return super(DeviceCheckPointIP, self).create(vals)

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
