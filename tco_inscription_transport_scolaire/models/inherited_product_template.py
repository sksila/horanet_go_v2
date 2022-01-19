# -*- coding: utf-8 -*-

# 1 : imports of python lib
import logging

# 2 :  imports of openerp
from odoo import models, fields, api, exceptions, _
from ..config import config

_logger = logging.getLogger(__name__)


class TCOProductTemplate(models.Model):
    """Surcharge du model product.template pour y ajouter les inscriptions TCO."""

    # region Private attributes
    _inherit = 'product.template'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    activate_tco = fields.Boolean(
        string="Activate tco inscription",
        default=False)
    tco_transport_titre = fields.Selection(
        string="tco transport titre",
        selection=config.INSCRIPTION_TRANSPORT_TITRE,
        default=None)

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    @api.constrains('tco_transport_titre', 'activate_tco')
    def _check_unicity_tco_config(self):
        """Check unicity of TCO inscription configuration (mapping).

        :return: ValidationError if duplicate
        """
        for rec in self:
            if rec.activate_tco:
                duplicate = self.search([('id', '!=', rec.id),
                                         ('activate_tco', '=', True),
                                         ('tco_transport_titre', '=', rec.tco_transport_titre)], limit=1)
                if duplicate:
                    raise exceptions.ValidationError(
                        _("Product template {name} has the same tco inscription configuration").format(
                            name=duplicate.name))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion

    pass
