# -*- coding: utf-8 -*-
import logging

from odoo import models, api
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class EcopadCacheUtility(models.AbstractModel):
    u"""Surcharge de la recherche des tags pour l'écopad."""

    # region Private attributes
    _inherit = 'horanet.environment.ecopad.cache.utility'

    # endregion

    # region Default methods

    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    @api.model
    def get_environment_tags_search_domain(self, search_tag_domain):
        u"""Surcharge de la méthode de recherche des tags de l'API ecopad pour filtrer par l'area fiscalité.

        Si le tag est de type calypso, alors ne garder que ceux dont l'area est 'area_calypso_fiscality'
        """
        result = super(EcopadCacheUtility, self).get_environment_tags_search_domain(search_tag_domain)

        area_fiscality = self.env.ref('calypso_amc_import.area_calypso_fiscality')
        techno_calypso = self.env.ref('calypso_amc_import.technology_calypso')

        filter_calypso_environment_tags = []
        # Filtre pour rechercher tout les tag sauf ceux de la technologie calypso dont on ne prend que la fiscalité
        calypso_environment_mapping_ids = self.env['partner.contact.identification.mapping'].search([
            '|',
            '&',
            ('area_id', '=', area_fiscality.id),
            ('technology_id', '=', techno_calypso.id),
            ('technology_id', '!=', techno_calypso.id)
        ]).ids
        if calypso_environment_mapping_ids:
            filter_calypso_environment_tags = [('mapping_id', 'in', calypso_environment_mapping_ids)]

        return expression.AND([result, filter_calypso_environment_tags])

    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
