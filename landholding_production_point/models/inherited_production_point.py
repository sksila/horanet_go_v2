# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductionPoint(models.Model):
    # region Private attributes
    _inherit = 'production.point'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    bati_id = fields.Many2one(string="Building", comodel_name='landholding.bati')
    city_id = fields.Many2one(string="City", related='bati_id.city_id', readonly=True)
    zip_id = fields.Many2one(string="Zip code", related='bati_id.zip_id', readonly=True)
    street_id = fields.Many2one(string="Street", related='bati_id.street_id', readonly=True)
    street2 = fields.Char(string='Additional address', related='bati_id.street2', readonly=True)
    street3 = fields.Char(string='Additional address', related='bati_id.street3', readonly=True)
    street_number_id = fields.Many2one(string=u"N°", related='bati_id.street_number_id', readonly=True)
    country_id = fields.Many2one(string="Country", related='bati_id.country_id', readonly=True)
    state_id = fields.Many2one(string="State", related='bati_id.state_id', readonly=True)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.onchange('bati_id')
    def _onchange_bati_id(self):
        """Set all the address related fields."""
        if self.bati_id:
            self.state_id = self.bati_id.state_id and self.bati_id.state_id.id or False
            self.zip_id = self.bati_id.zip_id and self.bati_id.zip_id.id or False
            self.street_id = self.bati_id.street_id and self.bati_id.street_id.id or False
            self.street_number_id = self.bati_id.street_number_id and self.bati_id.street_number_id.id or False
            self.city_id = self.bati_id.city_id and self.bati_id.city_id.id or False
            self.country_id = self.bati_id.country_id and self.bati_id.country_id.id or False
            self.street2 = self.bati_id.street2 or False
            self.street3 = self.bati_id.street3 or False
        else:
            self.state_id = False
            self.zip_id = False
            self.street_id = False
            self.street_number_id = False
            self.city_id = False
            self.country_id = False
            self.street2 = False
            self.street3 = False

    # region CRUD (overrides)
    # endregion

    # region Actions

    # endregion
    pass
