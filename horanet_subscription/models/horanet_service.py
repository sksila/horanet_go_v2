from odoo import models, fields, api, exceptions, _


class HoranetService(models.Model):
    # region Private attributes
    _name = 'horanet.service'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string="Name", required=True)
    product_uom_categ_id = fields.Many2one(string="Unit category", comodel_name='product.uom.categ', required=True)
    activity_ids = fields.Many2many(string="Activities", comodel_name='horanet.activity',
                                    relation='horanet_service_activity_rel',
                                    column1='service_id',
                                    column2='activity_id',
                                    domain="[('product_uom_categ_id', '=', product_uom_categ_id)]",
                                    required=True)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.onchange('product_uom_categ_id')
    def _filter_activities_by_product_category(self):
        """Filter activites by uom cateogory.

        Return a domain to filter on the activites' uom category from
        the service's uom category.
        """
        return {
            'domain': {
                'activity_ids': [('product_uom_categ_id', '=', self.product_uom_categ_id.id)]
            }
        }

    @api.onchange('product_uom_categ_id', 'activity_ids')
    def _check_unit_category(self):
        """Check if the unit category selected is the same as activities.

        :raise: odoo.exceptions.ValidationError if not
        """
        for service in self:
            activities_uom_category = service.mapped('activity_ids.product_uom_id.category_id')
            if len(activities_uom_category) > 1:
                raise exceptions.ValidationError(_('All activities must have the same unit category.'))
            elif service.activity_ids and service.product_uom_categ_id != activities_uom_category:
                raise exceptions.ValidationError(
                    _('The service must have same unit category as activities.'))

    @api.constrains('product_uom_categ_id', 'activity_ids')
    def _check_activities(self):
        """Check if activities are defined.

        For some reason, the `required=True` is not taken into account when
        creating service programatically.

        :raise: odoo.exceptions.ValidationError if not
        """
        self._check_unit_category()

        for service in self:
            if not service.activity_ids:
                raise exceptions.ValidationError(
                    _('Please add at least one activity to the service.')
                )

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
