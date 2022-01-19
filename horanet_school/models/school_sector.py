# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HoranetSchoolSector(models.Model):
    # region Private attributes
    _name = 'horanet.school.sector'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    name = fields.Char(string='Name', required=True)
    street_sector_ids = fields.Many2many(string='Streets sector', comodel_name='res.street.sector')

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
    @api.model
    def get_sectors(self, street_id, street_number):
        """Recherche temporaire (dev) de secteurs scolaire.

        :param street_id: object res.street id (integer)
        :param street_number: record res.street_number
        :param school_cycles: list of school_cycle
        :return: Corresponding school.sector or none
        """
        domain = []
        if street_id:
            # choix de rue
            domain.append(('street_sector_ids.street_id', '=', street_id.id))

        num_rue = street_number and int(filter(str.isdigit, str(street_number.name)))
        # TODO utiliser l'objet street_number (et regexp ou add calc field in street_number)
        if num_rue and isinstance(num_rue, int):
            # Pour les numéros impaire
            if num_rue % 2:
                domain.append(('street_sector_ids.odd_start', '<=', num_rue))
                domain.extend([
                    '|', '&',
                    ('street_sector_ids.odd_end', '!=', 0),
                    ('street_sector_ids.odd_end', '>=', num_rue),
                    ('street_sector_ids.odd_end', '=', 0)
                ])
            # Pour les numéros paire
            else:
                domain.append(('street_sector_ids.even_start', '<=', num_rue))
                domain.extend([
                    '|', '&',
                    ('street_sector_ids.even_end', '!=', 0),
                    ('street_sector_ids.even_end', '>=', num_rue),
                    ('street_sector_ids.even_end', '=', 0)
                ])
        sectors = self.search(domain)

        return sectors

    @api.model
    def get_partner_sectors_ids(self, partner_id):
        """Get the partner sectors by the location."""
        partner = self.env['res.partner'].browse(int(partner_id))
        sectors = self.get_sectors(partner.street_id.id, partner.street_number_id)
        return sectors.ids

    # endregion

    pass
